"""OpenAI Models 路由模块。"""

from fastapi import APIRouter, Depends
from duck2api.api.deps import verify_api_key
from duck2api.schemas.openai_models import ModelListResponse
from duck2api.services.model_service import model_service

router = APIRouter(prefix="/v1", tags=["Models"])


@router.get(
    "/models",
    response_model=ModelListResponse,
    dependencies=[Depends(verify_api_key)],
)
async def list_models():
    """获取所有可用模型列表。"""
    return await model_service.list_models()
