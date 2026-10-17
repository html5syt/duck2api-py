"""文件管理与上下文提取服务模块。

支持上传、查询、下载、删除文件，并在对话中作为多模态或文档上下文自动拼接。
"""

import time
from typing import Dict, List, Optional
from pydantic import BaseModel

from duck2api.schemas.openai_files import FileListResponse, FileObject
from duck2api.utils.helpers import current_timestamp_s, random_hex


class StoredFile(BaseModel):
    """文件存储实体。"""

    id: str
    filename: str
    content: bytes
    mime_type: str
    bytes_size: int
    created_at: int
    purpose: str = "assistants"


class FileService:
    """内存文件管理服务类。"""

    def __init__(self) -> None:
        self._store: Dict[str, StoredFile] = {}

    def upload_file(
        self,
        filename: str,
        content: bytes,
        mime_type: str = "application/octet-stream",
        purpose: str = "assistants",
    ) -> FileObject:
        """存储上传的文件并返回 FileObject。"""
        file_id = f"file-{random_hex(12)}"
        now = current_timestamp_s()

        record = StoredFile(
            id=file_id,
            filename=filename,
            content=content,
            mime_type=mime_type,
            bytes_size=len(content),
            created_at=now,
            purpose=purpose,
        )
        self._store[file_id] = record

        return FileObject(
            id=file_id,
            bytes=len(content),
            created_at=now,
            filename=filename,
            purpose=purpose,
        )

    def list_files(self) -> FileListResponse:
        """列出所有已保存的文件。"""
        items: List[FileObject] = []
        for f in self._store.values():
            items.append(
                FileObject(
                    id=f.id,
                    bytes=f.bytes_size,
                    created_at=f.created_at,
                    filename=f.filename,
                    purpose=f.purpose,
                )
            )
        return FileListResponse(object="list", data=items)

    def get_file(self, file_id: str) -> Optional[StoredFile]:
        """获取指定文件。"""
        return self._store.get(file_id)

    def delete_file(self, file_id: str) -> bool:
        """删除指定文件。"""
        if file_id in self._store:
            del self._store[file_id]
            return True
        return False

    def build_file_context(self, file_ids: List[str]) -> str:
        """根据 file_ids 提取并拼装文档上下文。"""
        if not file_ids:
            return ""

        context_blocks: List[str] = []
        for fid in file_ids:
            f = self.get_file(fid)
            if not f:
                continue

            # 纯文本/代码/JSON 文件解码
            try:
                text_content = f.content.decode("utf-8", errors="replace")
                if len(text_content) > 50000:
                    text_content = text_content[:50000] + "\n...(truncated)"
                context_blocks.append(f"[Attached File: {f.filename}]\n{text_content}")
            except Exception:
                context_blocks.append(f"[Attached Binary File: {f.filename} ({f.bytes_size} bytes)]")

        return "\n\n".join(context_blocks)


file_service = FileService()
