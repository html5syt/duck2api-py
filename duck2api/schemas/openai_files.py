"""OpenAI Files 协议数据模型。"""

from typing import List, Optional
from pydantic import BaseModel


class FileObject(BaseModel):
    """文件对象标准响应。"""

    id: str
    object: str = "file"
    bytes: int
    created_at: int
    filename: str
    purpose: str = "assistants"


class FileListResponse(BaseModel):
    """文件列表响应。"""

    object: str = "list"
    data: List[FileObject]


class FileDeleteResponse(BaseModel):
    """文件删除响应。"""

    id: str
    object: str = "file"
    deleted: bool = True
