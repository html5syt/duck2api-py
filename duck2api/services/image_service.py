"""图像生成与编辑服务模块。

通过 DuckDuckGo 的 GenerateImage 工具调用实现 OpenAI 兼容的文生图与图生图。
"""

import json
from typing import List, Optional
from duck2api.core.browser import browser_manager
from duck2api.core.models import ModelRegistry
from duck2api.schemas.duckgo import (
    ContentPart,
    DuckApiRequest,
    DuckMessage,
    DuckMetadata,
    DuckToolChoice,
)
from duck2api.schemas.openai_images import (
    ImageData,
    ImageEditRequest,
    ImageGenerationRequest,
    ImageResponse,
)
from duck2api.utils.helpers import current_timestamp_s
from duck2api.utils.logger import logger


class ImageService:
    """图像生成与编辑业务逻辑类。"""

    def __init__(self) -> None:
        self.browser = browser_manager

    async def generate_image(self, req: ImageGenerationRequest) -> ImageResponse:
        """执行文生图。"""
        real_model = ModelRegistry.resolve_model(req.model)
        tool_choice = DuckToolChoice(GenerateImage=True)

        duck_req = DuckApiRequest(
            model=real_model,
            messages=[
                DuckMessage(
                    role="user",
                    content=[ContentPart(type="text", text=req.prompt)],
                )
            ],
            metadata=DuckMetadata(toolChoice=tool_choice),
            canUseTools=True,
            reasoningEffort=ModelRegistry.map_reasoning_effort(req.reasoning_effort),
        )

        payload = duck_req.model_dump(by_alias=True, exclude_none=True)
        images_data, revised_prompt = await self._collect_images_from_stream(payload)

        if not images_data:
            # 若未直接产生图像工具结果，使用兜底提示
            logger.warning("No image data found in stream response")
            raise RuntimeError("No image was returned from upstream Duck.ai")

        return ImageResponse(
            created=current_timestamp_s(),
            data=images_data,
        )

    async def edit_image(self, req: ImageEditRequest) -> ImageResponse:
        """执行图生图或图像编辑。"""
        real_model = ModelRegistry.resolve_model(req.model)
        tool_choice = DuckToolChoice(GenerateImage=True)

        image_url = req.image
        if not image_url.startswith("data:"):
            image_url = f"data:image/png;base64,{image_url}"

        duck_req = DuckApiRequest(
            model=real_model,
            messages=[
                DuckMessage(
                    role="user",
                    content=[
                        ContentPart(type="text", text=req.prompt),
                        ContentPart(type="image", image=image_url, mimeType="image/png"),
                    ],
                )
            ],
            metadata=DuckMetadata(toolChoice=tool_choice),
            canUseTools=True,
            reasoningEffort=ModelRegistry.map_reasoning_effort(req.reasoning_effort),
        )

        payload = duck_req.model_dump(by_alias=True, exclude_none=True)
        images_data, revised_prompt = await self._collect_images_from_stream(payload)

        if not images_data:
            raise RuntimeError("No edited image was returned from upstream Duck.ai")

        return ImageResponse(
            created=current_timestamp_s(),
            data=images_data,
        )

    async def _collect_images_from_stream(self, payload: dict) -> tuple[List[ImageData], str]:
        """从上游 SSE 响应中提取图片 Base64 数据与提示词文本。"""
        images: List[ImageData] = []
        text_builder: List[str] = []

        async for chunk_str in self.browser.chat_stream(payload):
            lines = chunk_str.split("\n")
            for line in lines:
                line = line.strip()
                if not line.startswith("data:") or line == "data: [DONE]":
                    continue

                event_json = line[5:].strip()
                try:
                    data = json.loads(event_json)
                except Exception:
                    continue

                msg = data.get("message")
                if msg:
                    text_builder.append(msg)

                # 格式 1: parts 数组中的 generated-image
                parts = data.get("parts", [])
                for p in parts:
                    if isinstance(p, dict) and p.get("type") in ("generated-image", "image"):
                        b64 = p.get("result")
                        if not b64 and isinstance(p.get("data"), dict):
                            b64 = p["data"].get("b64Image")
                        if b64:
                            images.append(ImageData(b64_json=b64))

                # 格式 2: data 字段包含 b64Image
                raw_data = data.get("data")
                if isinstance(raw_data, dict):
                    b64 = raw_data.get("b64Image")
                    if b64:
                        images.append(ImageData(b64_json=b64))

        revised_text = "".join(text_builder).strip()
        for img in images:
            img.revised_prompt = revised_text

        return images, revised_text


image_service = ImageService()
