"""健康检查路由模块。"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class MessageResponse(BaseModel):
    message: str


@router.get("/", response_model=MessageResponse)
async def root_health():
    """根路径欢迎与健康探针。"""
    return {"message": "Hello, world!"}


@router.get("/ping", response_model=MessageResponse)
async def ping():
    """轻量心跳检测接口。"""
    return {"message": "pong"}
