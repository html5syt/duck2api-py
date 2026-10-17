"""OpenAI Audio 路由模块。"""

from typing import Optional
from fastapi import APIRouter, Depends, File, Form, UploadFile

from duck2api.api.deps import verify_api_key
from duck2api.schemas.openai_audio import TranscriptionResponse
from duck2api.services.audio_service import audio_service

router = APIRouter(prefix="/v1/audio", tags=["Audio"])


@router.post(
    "/transcriptions",
    response_model=TranscriptionResponse,
    dependencies=[Depends(verify_api_key)],
)
async def audio_transcriptions(
    file: UploadFile = File(...),
    model: Optional[str] = Form("whisper-1"),
    language: Optional[str] = Form(None),
    response_format: Optional[str] = Form("json"),
):
    """语音转文字接口（Whisper 协议兼容）。"""
    audio_bytes = await file.read()
    mime_type = file.content_type or "audio/webm"

    return await audio_service.transcribe(
        audio_bytes=audio_bytes,
        mime_type=mime_type,
    )
