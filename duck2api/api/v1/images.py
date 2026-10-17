"""OpenAI Images 路由模块。"""

import base64
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, Request, UploadFile

from duck2api.api.deps import verify_api_key
from duck2api.schemas.openai_images import (
    ImageEditRequest,
    ImageGenerationRequest,
    ImageResponse,
)
from duck2api.services.image_service import image_service

router = APIRouter(prefix="/v1/images", tags=["Images"])


@router.post(
    "/generations",
    response_model=ImageResponse,
    dependencies=[Depends(verify_api_key)],
)
async def generate_images(req: ImageGenerationRequest):
    """文本生成图片接口。"""
    return await image_service.generate_image(req)


@router.post(
    "/edits",
    response_model=ImageResponse,
    dependencies=[Depends(verify_api_key)],
)
async def edit_images(
    request: Request,
    image: Optional[UploadFile] = File(None),
    prompt: Optional[str] = Form(None),
    model: Optional[str] = Form("gpt-5.4-mini"),
    reasoning_effort: Optional[str] = Form("none"),
):
    """图像编辑/图生图接口（支持 Multipart 表单文件上传或 JSON 传输）。"""
    # 优先解析 Multipart 表单
    if image is not None and prompt is not None:
        file_bytes = await image.read()
        b64_image = base64.b64encode(file_bytes).decode("utf-8")
        req = ImageEditRequest(
            image=b64_image,
            prompt=prompt,
            model=model or "gpt-5.4-mini",
            reasoning_effort=reasoning_effort or "none",
        )
        return await image_service.edit_image(req)

    # 尝试解析 JSON 体
    body_data = await request.json()
    req = ImageEditRequest(**body_data)
    return await image_service.edit_image(req)
