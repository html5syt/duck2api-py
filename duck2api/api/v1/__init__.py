"""API v1 聚合路由模块。"""

from fastapi import APIRouter
from duck2api.api.v1.health import router as health_router
from duck2api.api.v1.models import router as models_router
from duck2api.api.v1.chat import router as chat_router
from duck2api.api.v1.responses import router as responses_router
from duck2api.api.v1.images import router as images_router
from duck2api.api.v1.files import router as files_router
from duck2api.api.v1.audio import router as audio_router

v1_router = APIRouter()

# 挂载各子业务路由
v1_router.include_router(health_router)
v1_router.include_router(models_router)
v1_router.include_router(chat_router)
v1_router.include_router(responses_router)
v1_router.include_router(images_router)
v1_router.include_router(files_router)
v1_router.include_router(audio_router)

__all__ = ["v1_router"]
