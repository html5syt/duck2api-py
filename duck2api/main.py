"""FastAPI 应用入口与生命周期管理模块。"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from duck2api.api import v1_router
from duck2api.api.middleware import TimingMiddleware
from duck2api.config.settings import settings
from duck2api.core.browser import browser_manager
from duck2api.utils.logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理，启动与清理全局 Playwright 浏览器池。"""
    logger.info("Initializing Duck2API gateway...")
    try:
        await browser_manager.start()
    except Exception as e:
        logger.error(f"Failed to pre-warm browser during startup: {e}. Requests will attempt on-demand start.")
    yield
    logger.info("Shutting down Duck2API gateway...")
    await browser_manager.close()


def create_app() -> FastAPI:
    """构建并配置 FastAPI 实例。"""
    app = FastAPI(
        title="Duck2API",
        version="1.0.0",
        description="基于 Playwright 原生浏览器引擎的现代化 DuckDuckGo 转 OpenAI 兼容 API 网关",
        lifespan=lifespan,
    )

    # 跨域 CORS 支持
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # 耗时统计中间件
    app.add_middleware(TimingMiddleware)

    # 注册标准路径路由
    app.include_router(v1_router)

    # 若指定前缀，额外挂载前缀路由
    if settings.prefix:
        prefix_clean = "/" + settings.prefix.strip("/")
        logger.info(f"Mounting routes with custom prefix: {prefix_clean}")
        app.include_router(v1_router, prefix=prefix_clean)

    return app


app = create_app()
