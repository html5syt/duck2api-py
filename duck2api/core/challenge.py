"""VQD JSA 挑战计算与解析模块。

在真实的 Playwright 浏览器环境中安全、完整地执行 DuckDuckGo 服务端下发的动态 JavaScript 挑战，
生成完全合规的 x-vqd-hash-1 凭证，彻底解决 418 风控校验。
"""

import base64
import json
from typing import Any, Dict, Optional
from duck2api.utils.logger import logger


# 在页面环境中执行挑战并生成解密后 token 的 JS 脚本
VQD_CHALLENGE_SOLVER_JS = """
async (challengeB64) => {
    const startMs = Date.now();
    let jsCode = "";
    try {
        jsCode = atob(challengeB64);
    } catch (e) {
        return { error: "Failed to decode base64 challenge: " + e.toString() };
    }

    const defaultStack = "Error\\nat l (https://duck.ai/dist/duckai-dist/entry.duckai.c0a8c794abcbc8ee2d3c.js:2:1446307)\\nat async https://duck.ai/dist/duckai-dist/entry.duckai.c0a8c794abcbc8ee2d3c.js:2:1294181";
    const origin = window.location.origin || "https://duck.ai";

    let rawResult;
    try {
        // 在真实浏览器沙箱中求值执行挑战函数
        rawResult = await (0, eval)(jsCode);
    } catch (err) {
        // 匹配官方回退逻辑
        const fallbackMsg = jsCode + "::" + (err.message || String(err)) + "::" + defaultStack + "::" + origin;
        return {
            token: btoa(fallbackMsg),
            isFallback: true,
            error: err.toString()
        };
    }

    if (!rawResult || typeof rawResult !== "object" || !Array.isArray(rawResult.client_hashes)) {
        const fallbackMsg = jsCode + "::InvalidChallengeResult::" + defaultStack + "::" + origin;
        return {
            token: btoa(fallbackMsg),
            isFallback: true,
            error: "Invalid result format"
        };
    }

    // 对 client_hashes 列表进行 SHA-256 并转 Base64 (使用原生 subtle crypto)
    const hashed = [];
    for (const val of rawResult.client_hashes) {
        try {
            const enc = new TextEncoder().encode(String(val));
            const digest = await crypto.subtle.digest("SHA-256", enc);
            const bytes = new Uint8Array(digest);
            let binary = "";
            for (let i = 0; i < bytes.byteLength; i++) {
                binary += String.fromCharCode(bytes[i]);
            }
            hashed.push(btoa(binary));
        } catch (e) {
            hashed.push("");
        }
    }

    const duration = Date.now() - startMs;
    const meta = Object.assign({}, rawResult.meta || {});
    meta.origin = origin;
    meta.duration = duration;
    meta.stack = defaultStack;

    const finalPayload = Object.assign({}, rawResult);
    finalPayload.client_hashes = hashed;
    finalPayload.meta = meta;

    try {
        const jsonStr = JSON.stringify(finalPayload);
        return {
            token: btoa(jsonStr),
            isFallback: false
        };
    } catch (e) {
        const fallbackMsg = jsCode + "::StringifyError::" + defaultStack + "::" + origin;
        return {
            token: btoa(fallbackMsg),
            isFallback: true,
            error: e.toString()
        };
    }
}
"""


class VQDChallengeSolver:
    """VQD 挑战求解器。"""

    @classmethod
    async def solve_in_page(cls, page, challenge_b64: str) -> str:
        """在给定的 Playwright 页面中求值挑战并返回 token。"""
        if not challenge_b64:
            raise ValueError("challenge_b64 cannot be empty")

        res: Dict[str, Any] = await page.evaluate(VQD_CHALLENGE_SOLVER_JS, challenge_b64)
        if res.get("isFallback"):
            logger.warning(f"VQD challenge evaluation used fallback: {res.get('error')}")

        token = res.get("token")
        if not token:
            raise RuntimeError(f"Failed to generate VQD token: {res.get('error')}")

        return token
