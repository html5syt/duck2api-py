"""语音识别与音频服务模块。

支持通过 Duck.ai 听写端点 (/duckchat/v1/dictation) 进行 Whisper 兼容的语音转文字。
"""

import json
from typing import Optional
from duck2api.core.browser import browser_manager
from duck2api.core.signals import SignalGenerator
from duck2api.schemas.openai_audio import TranscriptionResponse
from duck2api.utils.helpers import b64_encode
from duck2api.utils.logger import logger


class AudioService:
    """语音处理服务类。"""

    def __init__(self) -> None:
        self.browser = browser_manager

    async def transcribe(
        self,
        audio_bytes: bytes,
        mime_type: str = "audio/webm",
        max_retries: int = 2,
    ) -> TranscriptionResponse:
        """调用上游 /duckchat/v1/dictation 将音频转录为文本。"""
        audio_b64 = b64_encode(audio_bytes)

        dictation_js = """
        async ({ token, journeyId, feSignals, audioB64, mimeType }) => {
            // 将 base64 转回 Uint8Array 二进制
            const binaryStr = atob(audioB64);
            const len = binaryStr.length;
            const bytes = new Uint8Array(len);
            for (let i = 0; i < len; i++) {
                bytes[i] = binaryStr.charCodeAt(i);
            }

            const res = await fetch('/duckchat/v1/dictation', {
                method: 'POST',
                headers: {
                    'Content-Type': mimeType,
                    'Accept': 'application/json, text/plain, */*',
                    'x-vqd-hash-1': token,
                    'x-ddg-journey-id': journeyId,
                    'x-fe-signals': feSignals
                },
                body: bytes.buffer
            });

            const status = res.status;
            let data = null;
            let text = "";
            try {
                data = await res.json();
            } catch (e) {
                text = await res.text();
            }

            return { status, data, text };
        }
        """

        async with self.browser.get_page() as page:
            for attempt in range(max_retries + 1):
                token = await self.browser.fetch_vqd_token(page)
                journey_id = SignalGenerator.generate_journey_id()
                fe_signals = SignalGenerator.create_fe_signals()

                res = await page.evaluate(
                    dictation_js,
                    {
                        "token": token,
                        "journeyId": journey_id,
                        "feSignals": fe_signals,
                        "audioB64": audio_b64,
                        "mimeType": mime_type,
                    },
                )

                status = res.get("status")
                if status == 200:
                    data = res.get("data")
                    if isinstance(data, dict):
                        for key in ("text", "transcription", "result", "content"):
                            if key in data and data[key]:
                                return TranscriptionResponse(text=str(data[key]))
                    elif res.get("text"):
                        return TranscriptionResponse(text=res.get("text"))

                if status in (418, 429) and attempt < max_retries:
                    logger.warning(f"Dictation returned {status}, retrying ({attempt + 1}/{max_retries})...")
                    continue

                error_msg = res.get("text") or str(res.get("data"))
                raise RuntimeError(f"Audio transcription failed with status {status}: {error_msg}")

        raise RuntimeError("Transcription failed after maximum retries")


audio_service = AudioService()
