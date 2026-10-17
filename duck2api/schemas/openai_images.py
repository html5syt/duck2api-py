"""OpenAI Images 协议数据模型。"""

from typing import List, Optional
from pydantic import BaseModel


class ImageGenerationRequest(BaseModel):
    """文生图请求。"""

    prompt: str
    model: str = "gpt-5.4-mini"
    n: int = 1
    size: Optional[str] = "1024x1024"
    response_format: str = "b64_json"  # "b64_json" | "url"
    reasoning_effort: Optional[str] = "none"


class ImageEditRequest(BaseModel):
    """图像编辑/图生图请求。"""

    image: str  # Base64 图片数据
    prompt: str
    mask: Optional[str] = None
    model: str = "gpt-5.4-mini"
    n: int = 1
    size: Optional[str] = "1024x1024"
    response_format: str = "b64_json"
    reasoning_effort: Optional[str] = "none"


class ImageData(BaseModel):
    """单张图像返回体。"""

    b64_json: Optional[str] = None
    url: Optional[str] = None
    revised_prompt: Optional[str] = None


class ImageResponse(BaseModel):
    """图像生成/编辑标准响应体。"""

    created: int
    data: List[ImageData]
