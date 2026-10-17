"""中间件与全局异常处理模块。"""

import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from duck2api.utils.logger import logger


class TimingMiddleware(BaseHTTPMiddleware):
    """记录请求耗时并注入响应头。"""

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        try:
            response: Response = await call_next(request)
            duration_ms = int((time.time() - start_time) * 1000)
            response.headers["X-Response-Time-Ms"] = str(duration_ms)
            return response
        except Exception as exc:
            duration_ms = int((time.time() - start_time) * 1000)
            logger.exception(f"Unhandled server error on {request.method} {request.url.path}: {exc}")
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": str(exc),
                        "type": "internal_server_error",
                        "param": None,
                        "code": 500,
                    }
                },
                headers={"X-Response-Time-Ms": str(duration_ms)},
            )
