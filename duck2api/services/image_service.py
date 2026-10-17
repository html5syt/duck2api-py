"""图像生成与编辑服务模块。

通过 DuckDuckGo 的 GenerateImage 工具调用实现 OpenAI 兼容的文生图与图生图。
"""

import json
from typing import List, Tuple
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

    async def _collect_images_from_stream(self, payload: dict) -> Tuple[List[ImageData], str]:
        """从上游 SSE 响应中完整重组分块并提取图片 Base64 数据与提示词文本。"""
        raw_candidates: List[str] = []
        text_builder: List[str] = []
        buffer = ""

        async for chunk_str in self.browser.chat_stream(payload):
            buffer += chunk_str
            # 按换行严格切分完整行，处理跨 TCP 分包截断的超长 Base64 JSON 串
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line or not line.startswith("data:"):
                    continue
                if line == "data: [DONE]":
                    break

                raw_json = line[5:].strip()
                try:
                    event = json.loads(raw_json)
                except Exception:
                    # 分块尚未完全闭合或非 JSON，保留继续缓冲
                    continue

                msg = event.get("message")
                if msg:
                    text_builder.append(msg)

                # 1. 提取 event.data 中的图片数据
                data_field = event.get("data")
                if isinstance(data_field, dict):
                    for key in ("b64Image", "image", "result"):
                        val = data_field.get(key)
                        if val and isinstance(val, str) and len(val) > 100:
                            raw_candidates.append(val)
                elif isinstance(data_field, str) and "b64Image" in data_field:
                    try:
                        inner_data = json.loads(data_field)
                        if isinstance(inner_data, dict):
                            b64 = inner_data.get("b64Image")
                            if b64 and len(b64) > 100:
                                raw_candidates.append(b64)
                    except Exception:
                        pass

                # 2. 提取 event.parts 数组中的图片数据
                parts = event.get("parts", [])
                if isinstance(parts, list):
                    for p in parts:
                        if isinstance(p, dict):
                            res = p.get("result")
                            if res and len(res) > 100:
                                raw_candidates.append(res)
                            p_data = p.get("data")
                            if isinstance(p_data, dict):
                                b64 = p_data.get("b64Image")
                                if b64 and len(b64) > 100:
                                    raw_candidates.append(b64)

                # 3. 提取 event.result 字段
                result_field = event.get("result")
                if result_field and isinstance(result_field, str) and len(result_field) > 200:
                    raw_candidates.append(result_field)

        # 清洗 Base64 格式（移除可能携带的 data:image/xxx;base64, 前缀）
        clean_images: List[str] = []
        for img_str in raw_candidates:
            if "," in img_str and img_str.startswith("data:"):
                img_str = img_str.split(",", 1)[1]
            clean_images.append(img_str.strip())

        images: List[ImageData] = []
        if clean_images:
            # 当存在多张图片或由粗到精的预览图时，保留尺寸最大（最清晰）的最终生成结果
            best_img = max(clean_images, key=len)
            images.append(ImageData(b64_json=best_img))

        revised_text = "".join(text_builder).strip()
        for img in images:
            img.revised_prompt = revised_text

        return images, revised_text


image_service = ImageService()