"""OpenAI Audio 协议数据模型。"""

from typing import Optional
from pydantic import BaseModel


class TranscriptionResponse(BaseModel):
    """语音识别标准响应。"""

    text: str


class SpeechRequest(BaseModel):
    """文本转语音请求体。"""

    model: str = "tts-1"
    input: str
    voice: str = "alloy"
    response_format: str = "mp3"
    speed: float = 1.0
