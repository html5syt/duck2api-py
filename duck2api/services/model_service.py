"""模型列表查询服务模块。"""

from typing import List
from duck2api.core.browser import browser_manager
from duck2api.core.models import ModelRegistry
from duck2api.schemas.openai_models import ModelCard, ModelListResponse
from duck2api.utils.helpers import current_timestamp_s
from duck2api.utils.logger import logger


class ModelService:
    """模型列表服务类。"""

    def __init__(self) -> None:
        self.browser = browser_manager

    async def list_models(self) -> ModelListResponse:
        """获取并格式化当前支持的所有模型。"""
        created_ts = current_timestamp_s()
        cards: List[ModelCard] = []

        try:
            upstream_data = await self.browser.fetch_upstream_models()
            models_list = upstream_data.get("models", [])
            for m in models_list:
                model_id = m.get("id")
                if not model_id:
                    continue
                cards.append(
                    ModelCard(
                        id=model_id,
                        created=created_ts,
                        owned_by=m.get("provider", "duckduckgo"),
                        name=m.get("name"),
                        description=m.get("label"),
                    )
                )

            # 注入常用别名卡片，便于前端及 OpenAI 客户端提示
            for alias, target in ModelRegistry.ALIASES.items():
                cards.append(
                    ModelCard(
                        id=alias,
                        created=created_ts,
                        owned_by="alias",
                        name=f"{alias} (alias to {target})",
                    )
                )
        except Exception as e:
            logger.warning(f"Failed to fetch upstream models, using fallback registry: {e}")
            cards = ModelRegistry.get_fallback_cards(created_ts)

        return ModelListResponse(object="list", data=cards)


model_service = ModelService()
