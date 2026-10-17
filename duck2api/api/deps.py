"""API 依赖项注入模块。

提供 API Key 鉴权校验及服务实例依赖注入。
"""

from typing import Optional
from fastapi import Header, HTTPException, status
from duck2api.config.settings import settings


async def verify_api_key(
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> None:
    """校验请求头中的 Authorization Bearer Token。"""
    required_key = settings.effective_api_key
    if not required_key:
        # 未配置 API Key 则开放访问
        return

    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"message": "Missing Authorization header", "type": "auth_error"}},
        )

    token = authorization
    if token.startswith("Bearer "):
        token = token[7:].strip()

    if token != required_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"message": "Invalid API key", "type": "auth_error"}},
        )
