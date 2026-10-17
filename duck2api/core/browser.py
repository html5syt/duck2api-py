"""Playwright 原生浏览器管理器与页面池模块。

提供高性能的浏览器实例生命周期管理、页面复用池、自动重试与风控隔离机制。
"""

import asyncio
import json
import os
import sys
from contextlib import asynccontextmanager
from typing import Any, AsyncIterator, Dict, List, Optional
from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

from duck2api.config.settings import settings
from duck2api.core.challenge import VQDChallengeSolver
from duck2api.core.signals import SignalGenerator
from duck2api.utils.helpers import random_hex
from duck2api.utils.logger import logger


class BrowserManager:
    """基于 Playwright 的全局浏览器及页面池管理器。"""

    def __init__(self) -> None:
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._pool: asyncio.Queue[Page] = asyncio.Queue()
        self._all_pages: List[Page] = []
        self._lock = asyncio.Lock()
        self._is_running = False

    async def start(self) -> None:
        """启动浏览器及初始化页面池。"""
        async with self._lock:
            if self._is_running:
                return

            logger.info("Initializing Playwright browser manager...")
            self._playwright = await async_playwright().start()

            # 探测可用浏览器渠道
            channel = settings.browser_channel
            if not channel and sys.platform == "win32":
                # 在 Windows 下若无指定，默认检测系统 Edge
                channel = "msedge"

            launch_args = [
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-setuid-sandbox",
                "--no-first-run",
            ]

            proxy_config = None
            if settings.proxy_url:
                proxy_config = {"server": settings.proxy_url}
                logger.info(f"Using browser proxy: {settings.proxy_url}")

            launch_kwargs: Dict[str, Any] = {
                "headless": settings.browser_headless,
                "args": launch_args,
            }
            if channel:
                launch_kwargs["channel"] = channel
            if proxy_config:
                launch_kwargs["proxy"] = proxy_config

            try:
                self._browser = await self._playwright.chromium.launch(**launch_kwargs)
            except Exception as e:
                logger.warning(f"Failed to launch with channel={channel}: {e}. Retrying with default chromium...")
                launch_kwargs.pop("channel", None)
                self._browser = await self._playwright.chromium.launch(**launch_kwargs)

            # 创建全局隔离上下文
            context_kwargs: Dict[str, Any] = {
                "user_agent": settings.browser_user_agent,
                "locale": "zh-CN",
                "timezone_id": "Asia/Shanghai",
            }
            self._context = await self._browser.new_context(**context_kwargs)

            # 注入全量防检测 Stealth 脚本，解决 Linux / Docker 无头环境下的指纹特征暴露
            stealth_js = """
            // 1. 隐藏 webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
                configurable: true
            });

            // 2. 统一平台标识为 Win32 (与默认 Windows User-Agent 对齐，防止跨平台指纹冲突)
            Object.defineProperty(navigator, 'platform', {
                get: () => 'Win32',
                configurable: true
            });

            // 3. 补全 chrome 运行时特征
            if (!window.chrome) {
                window.chrome = {
                    runtime: {},
                    loadTimes: function() {},
                    csi: function() {},
                    app: {}
                };
            }

            // 4. 补全常用插件与语言列表
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
                configurable: true
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['zh-CN', 'zh', 'en-US', 'en'],
                configurable: true
            });
            """
            await self._context.add_init_script(stealth_js)

            # 预热并填充页面池
            pool_size = max(1, settings.page_pool_size)
            logger.info(f"Pre-warming page pool (target size: {pool_size})...")
            for i in range(pool_size):
                page = await self._create_ready_page()
                self._all_pages.append(page)
                await self._pool.put(page)

            self._is_running = True
            logger.info(f"Browser manager started successfully with {pool_size} ready pages.")

    async def _create_ready_page(self) -> Page:
        """创建并预加载 DuckDuckGo 站点的页面实例。"""
        assert self._context is not None
        page = await self._context.new_page()
        page.set_default_timeout(settings.browser_timeout_ms)

        # 仅拦截视频和大图，保留字体文件以确保 JSA 排版与文本测量检测完全通过
        async def route_filter(route):
            req = route.request
            resource_type = req.resource_type
            if resource_type in ("image", "media") and "duckchat" not in req.url:
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", route_filter)

        # 访问主站以建立域名同源环境与基本 Cookies
        try:
            await page.goto(settings.duck_base_url, wait_until="commit", timeout=settings.browser_timeout_ms)
            await page.wait_for_load_state("domcontentloaded")
        except Exception as e:
            logger.warning(f"Initial navigation warning: {e}")

        return page

    @asynccontextmanager
    async def get_page(self) -> AsyncIterator[Page]:
        """从页面池中获取一个可用的页面，并在使用后归还或回收。"""
        if not self._is_running:
            await self.start()

        page = await self._pool.get()
        is_healthy = True
        try:
            if page.is_closed():
                is_healthy = False
            yield page
        except Exception as e:
            logger.error(f"Error during page operation: {e}")
            is_healthy = False
            raise
        finally:
            if is_healthy and not page.is_closed():
                await self._pool.put(page)
            else:
                logger.info("Recycling unhealthy page and spawning a replacement...")
                try:
                    if not page.is_closed():
                        await page.close()
                except Exception:
                    pass
                if page in self._all_pages:
                    self._all_pages.remove(page)

                try:
                    new_page = await self._create_ready_page()
                    self._all_pages.append(new_page)
                    await self._pool.put(new_page)
                except Exception as e:
                    logger.error(f"Failed to spawn replacement page: {e}")

    async def fetch_vqd_token(self, page: Page) -> str:
        """在页面内发起 /duckchat/v1/status 请求并计算 VQD Hash。"""
        fetch_js = """
        async () => {
            const res = await fetch('/duckchat/v1/status', {
                headers: { 'x-vqd-accept': '1' }
            });
            return {
                status: res.status,
                vqdHash: res.headers.get('x-vqd-hash-1')
            };
        }
        """
        status_res = await page.evaluate(fetch_js)
        if status_res.get("status") != 200 or not status_res.get("vqdHash"):
            raise RuntimeError(f"Failed to get VQD challenge, status={status_res.get('status')}")

        vqd_hash = status_res["vqdHash"]
        token = await VQDChallengeSolver.solve_in_page(page, vqd_hash)
        return token

    async def fetch_upstream_models(self) -> Dict[str, Any]:
        """获取 DuckDuckGo 上游可用模型列表。"""
        async with self.get_page() as page:
            fetch_models_js = """
            async () => {
                const res = await fetch('/duckchat/v1/models');
                return {
                    status: res.status,
                    data: await res.json()
                };
            }
            """
            result = await page.evaluate(fetch_models_js)
            if result.get("status") != 200:
                raise RuntimeError(f"Upstream models returned status {result.get('status')}")
            return result.get("data", {})

    async def chat_stream(
        self,
        request_body: Dict[str, Any],
        max_retries: int = 2,
    ) -> AsyncIterator[str]:
        """执行流式聊天请求，通过页面内 ReadableStream 读取并实时产出 SSE 文本分块。"""
        queue: asyncio.Queue[str] = asyncio.Queue()
        callback_name = f"__py_chunk_{random_hex(8)}"

        async def on_stream_chunk(source, chunk: str):
            await queue.put(chunk)

        async with self.get_page() as page:
            await page.expose_binding(callback_name, on_stream_chunk)

            stream_worker_js = """
            async ({ token, journeyId, feSignals, payload, callbackName }) => {
                const send = window[callbackName];
                try {
                    const res = await fetch('/duckchat/v1/chat', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                            'Accept': 'text/event-stream',
                            'x-vqd-hash-1': token,
                            'x-ddg-journey-id': journeyId,
                            'x-fe-signals': feSignals
                        },
                        body: JSON.stringify(payload)
                    });

                    if (res.status !== 200) {
                        const errBody = await res.text();
                        await send(JSON.stringify({ __duck_error__: true, status: res.status, body: errBody }));
                        await send("__STREAM_EOF__");
                        return;
                    }

                    const reader = res.body.getReader();
                    const decoder = new TextDecoder();
                    while (true) {
                        const { done, value } = await reader.read();
                        if (done) break;
                        const chunkStr = decoder.decode(value, { stream: true });
                        if (chunkStr) {
                            await send(chunkStr);
                            if (chunkStr.includes('[DONE]')) {
                                try { reader.cancel(); } catch (e) {}
                                break;
                            }
                        }
                    }
                    await send("__STREAM_EOF__");
                } catch (e) {
                    await send(JSON.stringify({ __duck_error__: true, status: 500, body: e.toString() }));
                    await send("__STREAM_EOF__");
                }
            }
            """

            for attempt in range(max_retries + 1):
                # 每次重试前彻底清空队列中的残留数据，防止历史分块或 EOF 毒化新请求
                while not queue.empty():
                    try:
                        queue.get_nowait()
                    except asyncio.QueueEmpty:
                        break

                if attempt > 0:
                    # 遭遇上游风控或限制后进行退避延迟并重新刷新页面会话与 Cookies
                    logger.info(f"Refreshing page session for retry attempt {attempt}/{max_retries}...")
                    await asyncio.sleep(1.0 * attempt)
                    try:
                        await page.goto(settings.duck_base_url, wait_until="commit", timeout=settings.browser_timeout_ms)
                        await page.wait_for_load_state("domcontentloaded")
                    except Exception as e:
                        logger.warning(f"Page reload warning on retry: {e}")

                try:
                    token = await self.fetch_vqd_token(page)
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"Failed to fetch VQD on attempt {attempt}: {e}, retrying...")
                        continue
                    raise

                journey_id = SignalGenerator.generate_journey_id()
                fe_signals = SignalGenerator.create_fe_signals()

                worker_params = {
                    "token": token,
                    "journeyId": journey_id,
                    "feSignals": fe_signals,
                    "payload": request_body,
                    "callbackName": callback_name,
                }

                stream_task = asyncio.create_task(page.evaluate(stream_worker_js, worker_params))

                is_retryable_error = False
                error_chunk_to_yield = None

                while True:
                    chunk = await queue.get()
                    if chunk == "__STREAM_EOF__":
                        break

                    # 探测错误分块
                    if "__duck_error__" in chunk:
                        try:
                            err_data = json.loads(chunk)
                            status = err_data.get("status")
                            if status in (418, 429) and attempt < max_retries:
                                logger.warning(f"Upstream returned {status}, retrying ({attempt + 1}/{max_retries})...")
                                is_retryable_error = True
                                break
                            error_chunk_to_yield = chunk
                        except Exception:
                            pass

                    yield chunk

                await stream_task

                if not is_retryable_error:
                    if error_chunk_to_yield:
                        logger.error(f"Upstream final error chunk: {error_chunk_to_yield}")
                    break

    async def close(self) -> None:
        """关闭所有页面与浏览器实例。"""
        async with self._lock:
            if not self._is_running:
                return

            logger.info("Closing browser manager...")
            self._is_running = False

            while not self._pool.empty():
                try:
                    p = self._pool.get_nowait()
                    if not p.is_closed():
                        await p.close()
                except Exception:
                    pass

            if self._context:
                await self._context.close()
            if self._browser:
                await self._browser.close()
            if self._playwright:
                await self._playwright.stop()

            logger.info("Browser manager closed cleanly.")


# 全局单例
browser_manager = BrowserManager()