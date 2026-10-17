"""OpenAI Chat Completions 协议数据模型。"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """对话消息结构。"""

    role: str
    content: Union[str, List[Dict[str, Any]], None] = None
    name: Optional[str] = None


class UsageInfo(BaseModel):
    """Token 消耗统计。"""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    prompt_tokens_details: Optional[Dict[str, Any]] = None


class ChatCompletionRequest(BaseModel):
    """Chat Completions 请求体。"""

    model: str
    messages: List[ChatMessage]
    stream: bool = False
    temperature: Optional[float] = None
    top_p: Optional[float] = None
    max_tokens: Optional[int] = None
    reasoning_effort: Optional[str] = None
    web_search: Optional[bool] = None
    file_ids: Optional[List[str]] = None


class ChatCompletionResponseChoice(BaseModel):
    """非流式响应候选项。"""

    index: int = 0
    message: ChatMessage
    finish_reason: Optional[str] = "stop"


class ChatCompletionResponse(BaseModel):
    """OpenAI 标准非流式响应。"""

    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionResponseChoice]
    usage: UsageInfo


class ChatCompletionChunkDelta(BaseModel):
    """流式增量。"""

    role: Optional[str] = None
    content: Optional[str] = None


class ChatCompletionChunkChoice(BaseModel):
    """流式响应候选项。"""

    index: int = 0
    delta: ChatCompletionChunkDelta
    finish_reason: Optional[str] = None


class ChatCompletionChunk(BaseModel):
    """OpenAI 标准流式分块。"""

    id: str
    object: str = "chat.completion.chunk"
    created: int
    model: str
    choices: List[ChatCompletionChunkChoice]
    usage: Optional[UsageInfo] = None
