"""通用辅助函数模块。"""

import base64
import hashlib
import json
import secrets
import time
from typing import Any, Dict


def random_hex(byte_length: int = 16) -> str:
    """生成指定字节长度的安全随机十六进制字符串。"""
    return secrets.token_hex(byte_length)


def b64_encode(data: bytes | str) -> str:
    """Base64 编码字符串或字节串。"""
    if isinstance(data, str):
        data = data.encode("utf-8")
    return base64.b64encode(data).decode("utf-8")


def b64_decode(data: str) -> str:
    """Base64 解码为 UTF-8 字符串。"""
    return base64.b64decode(data.encode("utf-8")).decode("utf-8", errors="replace")


def current_timestamp_ms() -> int:
    """获取当前毫秒级时间戳。"""
    return int(time.time() * 1000)


def current_timestamp_s() -> int:
    """获取当前秒级 Unix 时间戳。"""
    return int(time.time())


def md5_hash(text: str) -> str:
    """计算字符串的 MD5 哈希。"""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def sha256_hash(text: str) -> str:
    """计算字符串的 SHA-256 十六进制哈希。"""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
