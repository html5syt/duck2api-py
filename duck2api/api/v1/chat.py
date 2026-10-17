"""OpenAI Chat Completions 路由模块。"""

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from duck2api.api.deps import verify_api_key
from duck2api.schemas.openai_chat import ChatCompletionRequest, ChatCompletionResponse
from duck2api.services.chat_service import chat_service
from duck2api.services.file_service import file_service

router = APIRouter(prefix="/v1", tags=["Chat"])


@router.post(
    "/chat/completions",
    response_model=ChatCompletionResponse,
    dependencies=[Depends(verify_api_key)],
)
async def create_chat_completion(req: ChatCompletionRequest):
    """创建对话补全任务（支持流式、非流式、推理模式、网络搜索与文件引用）。"""
    file_context = ""
    if req.file_ids:
        file_context = file_service.build_file_context(req.file_ids)

    if req.stream:
        return StreamingResponse(
            chat_service.stream_chat(req, file_context),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Content-Type": "text/event-stream; charset=utf-8",
            },
        )

    return await chat_service.complete_chat(req, file_context)
