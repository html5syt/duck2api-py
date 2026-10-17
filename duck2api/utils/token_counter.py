"""Token 估算与 Prompt 缓存统计模块。"""

import hashlib
from typing import Any, List, Union


def count_tokens(text: str) -> int:
    """快速估算文本 Token 数量。

    英文按单词/4字符估算，中文字符按 1 字符 ≈ 1 Token 估算。
    """
    if not text:
        return 0

    cjk_count = 0
    non_cjk_count = 0
    for char in text:
        if "\u4e00" <= char <= "\u9fff":
            cjk_count += 1
        else:
            non_cjk_count += 1

    return cjk_count + max(1, (non_cjk_count + 3) // 4)


def message_text(content: Union[str, List[Any], None]) -> str:
    """提取消息中的纯文本内容。"""
    if not content:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for part in content:
            if isinstance(part, dict):
                if part.get("type") == "text":
                    parts.append(part.get("text", ""))
                elif part.get("type") == "image_url":
                    parts.append("[image]")
            elif isinstance(part, str):
                parts.append(part)
        return " ".join(parts)
    return str(content)


def count_messages_tokens(messages: List[Any]) -> int:
    """估算整个消息数组的 Token 总数（包含角色与结构开销）。"""
    total = 3  # baseline conversation tokens
    for msg in messages:
        total += 4  # message overhead
        if isinstance(msg, dict):
            content = msg.get("content")
        else:
            content = getattr(msg, "content", "")
        total += count_tokens(message_text(content))
    return total


def hash_prompt(text: str) -> str:
    """计算 Prompt 摘要哈希，用于统计和缓存追踪。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
