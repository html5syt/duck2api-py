"""OpenAI Files 路由模块。"""

from fastapi import APIRouter, Depends, File, Form, HTTPException, Response, UploadFile

from duck2api.api.deps import verify_api_key
from duck2api.schemas.openai_files import (
    FileDeleteResponse,
    FileListResponse,
    FileObject,
)
from duck2api.services.file_service import file_service

router = APIRouter(prefix="/v1/files", tags=["Files"])


@router.post(
    "",
    response_model=FileObject,
    dependencies=[Depends(verify_api_key)],
)
async def upload_file(
    file: UploadFile = File(...),
    purpose: str = Form("assistants"),
):
    """上传文件用于对话问答或多模态引用。"""
    content = await file.read()
    filename = file.filename or "unknown_file"
    mime_type = file.content_type or "application/octet-stream"

    return file_service.upload_file(
        filename=filename,
        content=content,
        mime_type=mime_type,
        purpose=purpose,
    )


@router.get(
    "",
    response_model=FileListResponse,
    dependencies=[Depends(verify_api_key)],
)
async def list_files():
    """获取已上传的文件列表。"""
    return file_service.list_files()


@router.get(
    "/{file_id}",
    response_model=FileObject,
    dependencies=[Depends(verify_api_key)],
)
async def get_file(file_id: str):
    """获取指定文件元数据。"""
    f = file_service.get_file(file_id)
    if not f:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": f"File '{file_id}' not found", "type": "not_found_error"}},
        )
    return FileObject(
        id=f.id,
        bytes=f.bytes_size,
        created_at=f.created_at,
        filename=f.filename,
        purpose=f.purpose,
    )


@router.delete(
    "/{file_id}",
    response_model=FileDeleteResponse,
    dependencies=[Depends(verify_api_key)],
)
async def delete_file(file_id: str):
    """删除指定文件。"""
    deleted = file_service.delete_file(file_id)
    if not deleted:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": f"File '{file_id}' not found", "type": "not_found_error"}},
        )
    return FileDeleteResponse(id=file_id, deleted=True)


@router.get(
    "/{file_id}/content",
    dependencies=[Depends(verify_api_key)],
)
async def get_file_content(file_id: str):
    """下载指定文件原始内容。"""
    f = file_service.get_file(file_id)
    if not f:
        raise HTTPException(
            status_code=404,
            detail={"error": {"message": f"File '{file_id}' not found", "type": "not_found_error"}},
        )

    return Response(
        content=f.content,
        media_type=f.mime_type,
        headers={"Content-Disposition": f'attachment; filename="{f.filename}"'},
    )
