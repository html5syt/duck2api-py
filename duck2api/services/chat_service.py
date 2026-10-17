"""Chat Completions 业务服务模块。

负责 OpenAI 协议到 DuckDuckGo 协议的双向转换、流式分块翻译及 Token/时间遥测。
"""

import json
import time
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from duck2api.core.browser import browser_manager
from duck2api.core.models import ModelRegistry
from duck2api.schemas.duckgo import (
    ContentPart,
    DuckApiRequest,
    DuckMessage,
    DuckMetadata,
    DuckToolChoice,
)
from duck2api.schemas.openai_chat import (
    ChatCompletionChunk,
    ChatCompletionChunkChoice,
    ChatCompletionChunkDelta,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseChoice,
    ChatMessage,
    UsageInfo,
)
from duck2api.utils.helpers import current_timestamp_s, random_hex
from duck2api.utils.logger import logger
from duck2api.utils.token_counter import count_messages_tokens, count_tokens


class ChatService:
    """Chat Completions 核心业务逻辑类。"""

    def __init__(self) -> None:
        self.browser = browser_manager

    def build_duck_request(
        self,
        req: ChatCompletionRequest,
        extra_file_context: Optional[str] = None,
    ) -> Dict[str, Any]:
        """将 OpenAI 请求体转换为 DuckDuckGo 兼容的请求载荷。"""
        real_model = ModelRegistry.resolve_model(req.model)
        reasoning_effort = ModelRegistry.map_reasoning_effort(req.reasoning_effort)

        tool_choice = DuckToolChoice()
        if req.web_search:
            tool_choice.WebSearch = True

        duck_messages: List[DuckMessage] = []

        # 处理 system 消息与普通消息
        for idx, msg in enumerate(req.messages):
            role = msg.role
            # Duck 仅支持 user / assistant 角色，将 system 转为首条 user 提示
            if role == "system":
                role = "user"
            elif role not in ("user", "assistant"):
                continue

            content = msg.content
            parts: List[ContentPart] = []

            # 纯文本消息
            if isinstance(content, str):
                text_val = content
                # 若为最后一条 user 消息且存在附加文件内容，拼接到末尾
                if extra_file_context and idx == len(req.messages) - 1 and role == "user":
                    text_val = f"{text_val}\n\n{extra_file_context}"
                parts.append(ContentPart(type="text", text=text_val))

            # 多模态消息
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict):
                        item_type = item.get("type", "text")
                        if item_type == "text":
                            parts.append(ContentPart(type="text", text=item.get("text", "")))
                        elif item_type == "image_url":
                            img_obj = item.get("image_url", {})
                            url = img_obj.get("url", "")
                            parts.append(ContentPart(type="image", image=url, mimeType="image/png"))
                    elif isinstance(item, str):
                        parts.append(ContentPart(type="text", text=item))

            if parts:
                duck_messages.append(DuckMessage(role=role, content=parts))

        duck_req = DuckApiRequest(
            model=real_model,
            messages=duck_messages,
            metadata=DuckMetadata(toolChoice=tool_choice),
            canUseTools=True,
            reasoningEffort=reasoning_effort,
        )

        return duck_req.model_dump(by_alias=True, exclude_none=True)

    async def stream_chat(
        self,
        req: ChatCompletionRequest,
        extra_file_context: Optional[str] = None,
    ) -> AsyncIterator[str]:
        """执行流式对话，实时产出符合 OpenAI 标准的 SSE 数据行。"""
        chat_id = f"chatcmpl-{random_hex(12)}"
        created_ts = current_timestamp_s()
        real_model = ModelRegistry.resolve_model(req.model)
        payload = self.build_duck_request(req, extra_file_context)

        prompt_tokens = count_messages_tokens(req.messages)
        accumulated_text = ""
        is_first_chunk = True
        stream_buffer = ""

        async for raw_chunk in self.browser.chat_stream(payload):
            stream_buffer += raw_chunk
            while "\n" in stream_buffer:
                line, stream_buffer = stream_buffer.split("\n", 1)
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue

                event_data = line[5:].strip()
                if event_data == "[DONE]":
                    stop_chunk = ChatCompletionChunk(
                        id=chat_id,
                        created=created_ts,
                        model=real_model,
                        choices=[
                            ChatCompletionChunkChoice(
                                index=0,
                                delta=ChatCompletionChunkDelta(),
                                finish_reason="stop",
                            )
                        ],
                    )
                    yield f"data: {stop_chunk.model_dump_json(exclude_none=True)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                try:
                    parsed = json.loads(event_data)
                except Exception:
                    continue

                # 检查上游错误
                if parsed.get("action") == "error":
                    err_type = parsed.get("type", "upstream_error")
                    logger.error(f"Duck upstream error: {parsed}")
                    err_chunk = ChatCompletionChunk(
                        id=chat_id,
                        created=created_ts,
                        model=real_model,
                        choices=[
                            ChatCompletionChunkChoice(
                                index=0,
                                delta=ChatCompletionChunkDelta(content=f"\n[Error: {err_type}]"),
                                finish_reason="error",
                            )
                        ],
                    )
                    yield f"data: {err_chunk.model_dump_json(exclude_none=True)}\n\n"
                    yield "data: [DONE]\n\n"
                    return

                delta_msg = parsed.get("message", "")
                if not delta_msg:
                    continue

                accumulated_text += delta_msg

                # 构造标准分块
                delta_payload = ChatCompletionChunkDelta(content=delta_msg)
                if is_first_chunk:
                    delta_payload.role = "assistant"
                    is_first_chunk = False

                chunk_obj = ChatCompletionChunk(
                    id=chat_id,
                    created=created_ts,
                    model=real_model,
                    choices=[
                        ChatCompletionChunkChoice(
                            index=0,
                            delta=delta_payload,
                            finish_reason=None,
                        )
                    ],
                )
                yield f"data: {chunk_obj.model_dump_json(exclude_none=True)}\n\n"

        # 兜底结束
        yield "data: [DONE]\n\n"

    async def complete_chat(
        self,
        req: ChatCompletionRequest,
        extra_file_context: Optional[str] = None,
    ) -> ChatCompletionResponse:
        """执行非流式对话，收集全部内容后返回完整 ChatCompletionResponse。"""
        chat_id = f"chatcmpl-{random_hex(12)}"
        created_ts = current_timestamp_s()
        real_model = ModelRegistry.resolve_model(req.model)
        prompt_tokens = count_messages_tokens(req.messages)

        full_text_parts: List[str] = []

        async for chunk_str in self.stream_chat(req, extra_file_context):
            lines = chunk_str.split("\n")
            for line in lines:
                line = line.strip()
                if not line.startswith("data:") or line == "data: [DONE]":
                    continue
                try:
                    data = json.loads(line[5:].strip())
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        content = delta.get("content")
                        if content:
                            full_text_parts.append(content)
                except Exception:
                    pass

        full_text = "".join(full_text_parts)
        completion_tokens = count_tokens(full_text)

        return ChatCompletionResponse(
            id=chat_id,
            created=created_ts,
            model=real_model,
            choices=[
                ChatCompletionResponseChoice(
                    index=0,
                    message=ChatMessage(role="assistant", content=full_text),
                    finish_reason="stop",
                )
            ],
            usage=UsageInfo(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )


chat_service = ChatService()