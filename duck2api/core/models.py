"""模型目录与映射规则模块。

支持动态获取上游可用模型、别名转换以及推理级别调整。
"""

from typing import Dict, List, Optional
from duck2api.schemas.openai_models import ModelCard


class ModelRegistry:
    """模型注册与映射管理器。"""

    # 默认映射表（OpenAI 常见模型与别名映射到当前 DuckDuckGo 支持的模型）
    ALIASES: Dict[str, str] = {
        "gpt-4o-mini": "gpt-5.4-mini",
        "gpt-4o": "gpt-6-luna",
        "gpt-4": "gpt-5.4-mini",
        "gpt-3.5-turbo": "gpt-5.4-mini",
        "gpt-5.4-nano": "gpt-5.4-mini",
        "gpt-5-mini": "gpt-5.4-mini",
        "claude-3-haiku": "claude-haiku-4-5",
        "claude-3-haiku-20240307": "claude-haiku-4-5",
        "claude-3-5-haiku": "claude-haiku-4-5",
        "claude-3.5-haiku": "claude-haiku-4-5",
        "mistral-small": "mistral-small-2603",
        "mistralai/mistral-small-24b-instruct-2501": "mistral-small-2603",
        "llama-3.3-70b": "tinfoil/gpt-oss-120b",
        "meta-llama/llama-3.3-70b-instruct-turbo": "tinfoil/gpt-oss-120b",
        "gemma": "tinfoil/gemma4-31b",
        "gemma4": "tinfoil/gemma4-31b",
    }

    # 默认兜底模型列表（在上游接口临时不可用时提供）
    FALLBACK_MODELS: List[Dict[str, str]] = [
        {"id": "gpt-5.4-mini", "owned_by": "openai", "name": "GPT-5.4 mini"},
        {"id": "gpt-6-luna", "owned_by": "openai", "name": "GPT-6 Luna"},
        {"id": "claude-haiku-4-5", "owned_by": "anthropic", "name": "Claude Haiku 4.5"},
        {"id": "mistral-small-2603", "owned_by": "mistral", "name": "Mistral Small 4"},
        {"id": "tinfoil/gpt-oss-120b", "owned_by": "tinfoil", "name": "gpt-oss 120B"},
        {"id": "tinfoil/gemma4-31b", "owned_by": "tinfoil", "name": "Gemma 4 31B"},
    ]

    @classmethod
    def resolve_model(cls, model_name: str) -> str:
        """将用户请求的模型名称解析为 DuckDuckGo 真实支持的模型 ID。"""
        if not model_name:
            return "gpt-5.4-mini"

        clean_name = model_name.strip().lower()
        if clean_name in cls.ALIASES:
            return cls.ALIASES[clean_name]

        # 检查部分前缀匹配
        for alias, target in cls.ALIASES.items():
            if clean_name.startswith(alias):
                return target

        return model_name.strip()

    @classmethod
    def map_reasoning_effort(cls, effort: Optional[str]) -> str:
        """调整 reasoning_effort 参数以符合 DuckDuckGo 限制。

        DuckDuckGo 免费层通常仅支持 "none"（快速）或 "low"（思考/推理）。
        """
        if not effort:
            return "none"
        effort_lower = effort.strip().lower()
        if effort_lower in ("none", "false", "off"):
            return "none"
        if effort_lower in ("low", "medium", "high", "max", "xhigh", "true"):
            return "low"
        return "none"

    @classmethod
    def get_fallback_cards(cls, created_ts: int) -> List[ModelCard]:
        """获取兜底模型卡片列表。"""
        cards: List[ModelCard] = []
        for m in cls.FALLBACK_MODELS:
            cards.append(
                ModelCard(
                    id=m["id"],
                    created=created_ts,
                    owned_by=m["owned_by"],
                    name=m["name"],
                )
            )
        # 补充主要别名
        for alias in ["gpt-4o-mini", "claude-3-haiku", "gpt-3.5-turbo"]:
            cards.append(
                ModelCard(
                    id=alias,
                    created=created_ts,
                    owned_by="duck2api-alias",
                    name=f"{alias} (alias to {cls.ALIASES.get(alias)})",
                )
            )
        return cards
