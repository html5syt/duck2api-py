"""DuckDuckGo AI Chat 内部协议数据模型。"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ContentPart(BaseModel):
    """多模态内容组件。"""

    type: str = "text"  # "text", "image", "file"
    text: Optional[str] = None
    image: Optional[str] = None  # data URL
    mimeType: Optional[str] = None
    filename: Optional[str] = None


class DuckMessage(BaseModel):
    """DuckDuckGo 消息体。"""

    role: str  # "user" | "assistant"
    content: Union[str, List[ContentPart]]


class DuckToolChoice(BaseModel):
    """工具启用选项。"""

    GenerateImage: Optional[bool] = None
    WebSearch: Optional[bool] = None
    NewsSearch: bool = False
    VideosSearch: bool = False
    LocalSearch: bool = False
    WeatherForecast: bool = False


class DuckMetadata(BaseModel):
    """Duck 上游请求元数据。"""

    toolChoice: DuckToolChoice = Field(default_factory=DuckToolChoice)


class DuckApiRequest(BaseModel):
    """DuckDuckGo /duckchat/v1/chat 上游完整请求结构。"""

    model: str
    messages: List[DuckMessage]
    metadata: DuckMetadata = Field(default_factory=DuckMetadata)
    canUseTools: bool = True
    reasoningEffort: str = "none"  # "none" | "low" | "medium"
    canUseApproxLocation: Optional[bool] = None
    canDelegateImageGeneration: Optional[bool] = None


class ImagePartData(BaseModel):
    """生成的图片详细数据。"""

    b64Image: Optional[str] = None
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    status: Optional[str] = None
    title: Optional[str] = None
    type: Optional[str] = None


class ImagePart(BaseModel):
    """图片组件结构。"""

    type: str
    result: Optional[str] = None
    format: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    data: Optional[ImagePartData] = None


class DuckApiResponse(BaseModel):
    """DuckDuckGo SSE 返回事件解码模型。"""

    id: Optional[str] = None
    action: Optional[str] = None
    status: Optional[int] = None
    model: Optional[str] = None
    role: Optional[str] = None
    message: Optional[str] = None
    created: Optional[int] = None
    toolName: Optional[str] = None
    toolCallId: Optional[str] = None
    result: Optional[str] = None
    parts: Optional[List[ImagePart]] = None
    data: Optional[Any] = None
    error: Optional[str] = None
    type: Optional[str] = None
