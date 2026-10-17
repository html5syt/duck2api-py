"""OpenAI Responses API 路由模块。"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from duck2api.api.deps import verify_api_key
from duck2api.schemas.openai_responses import ResponseAPIRequest, ResponseAPIResponse
from duck2api.services.responses_service import responses_service

router = APIRouter(prefix="/v1", tags=["Responses"])


@router.post(
    "/responses",
    response_model=ResponseAPIResponse,
    dependencies=[Depends(verify_api_key)],
)
async def create_responses(req: ResponseAPIRequest):
    """创建 Responses API 响应任务。"""
    if req.stream:
        return StreamingResponse(
            responses_service.stream_responses(req),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream; charset=utf-8",
            },
        )

    return await responses_service.complete_responses(req)
