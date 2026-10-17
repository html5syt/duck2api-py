"""OpenAI Models 协议数据模型。"""

from typing import List, Optional
from pydantic import BaseModel


class ModelCard(BaseModel):
    """单个模型描述卡片。"""

    id: str
    object: str = "model"
    created: int
    owned_by: str = "openai"
    name: Optional[str] = None
    description: Optional[str] = None


class ModelListResponse(BaseModel):
    """模型列表响应。"""

    object: str = "list"
    data: List[ModelCard]
