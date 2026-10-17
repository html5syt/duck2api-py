"""OpenAI Responses API 协议数据模型。"""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel


class ResponseAPIRequest(BaseModel):
    """Responses API 请求体。"""

    model: str
    input: Union[str, List[Any]]
    instructions: Optional[str] = None
    stream: bool = False
    temperature: Optional[float] = None


class ResponseAPIResponse(BaseModel):
    """Responses API 响应体。"""

    id: str
    object: str = "response"
    created: int
    model: str
    output: List[Dict[str, Any]]
