"""OpenAI Responses API 业务服务模块。"""

from typing import Any, AsyncIterator, Dict, List, Union
from duck2api.schemas.openai_chat import ChatCompletionRequest, ChatMessage
from duck2api.schemas.openai_responses import ResponseAPIRequest, ResponseAPIResponse
from duck2api.services.chat_service import chat_service
from duck2api.utils.helpers import current_timestamp_s, random_hex


class ResponsesService:
    """Responses API 逻辑处理类。"""

    def __init__(self) -> None:
        self.chat_service = chat_service

    def _convert_to_chat_request(self, req: ResponseAPIRequest) -> ChatCompletionRequest:
        """将 Responses API 请求转换为内部 ChatCompletionRequest。"""
        messages: List[ChatMessage] = []

        if req.instructions:
            messages.append(ChatMessage(role="system", content=req.instructions))

        user_content: Union[str, List[Dict[str, Any]]]
        if isinstance(req.input, str):
            user_content = req.input
        elif isinstance(req.input, list):
            # 将 input 列表元素规整化
            converted_list: List[Dict[str, Any]] = []
            for item in req.input:
                if isinstance(item, str):
                    converted_list.append({"type": "text", "text": item})
                elif isinstance(item, dict):
                    converted_list.append(item)
            user_content = converted_list
        else:
            user_content = str(req.input)

        messages.append(ChatMessage(role="user", content=user_content))

        return ChatCompletionRequest(
            model=req.model,
            messages=messages,
            stream=req.stream,
            temperature=req.temperature,
        )

    async def complete_responses(self, req: ResponseAPIRequest) -> ResponseAPIResponse:
        """非流式处理 Responses API。"""
        chat_req = self._convert_to_chat_request(req)
        chat_resp = await self.chat_service.complete_chat(chat_req)

        resp_id = f"resp-{random_hex(12)}"
        content = ""
        if chat_resp.choices:
            content = str(chat_resp.choices[0].message.content or "")

        return ResponseAPIResponse(
            id=resp_id,
            created=current_timestamp_s(),
            model=chat_resp.model,
            output=[
                {
                    "type": "message",
                    "id": f"msg_{random_hex(10)}",
                    "role": "assistant",
                    "content": [{"type": "text", "text": content}],
                }
            ],
        )

    async def stream_responses(self, req: ResponseAPIRequest) -> AsyncIterator[str]:
        """流式处理 Responses API。"""
        chat_req = self._convert_to_chat_request(req)
        async for chunk in self.chat_service.stream_chat(chat_req):
            yield chunk


responses_service = ResponsesService()
