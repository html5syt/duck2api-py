"""配置与通用工具模块测试用例。"""

import pytest
from duck2api.config.settings import Settings
from duck2api.utils.helpers import (
    b64_decode,
    b64_encode,
    current_timestamp_ms,
    current_timestamp_s,
    random_hex,
    sha256_hash,
)
from duck2api.utils.token_counter import (
    count_messages_tokens,
    count_tokens,
    hash_prompt,
    message_text,
)


def test_settings_api_key_bearer():
    """测试带有 Bearer 前缀的鉴权密钥解析。"""
    s = Settings(authorization="Bearer test_token_12345")
    assert s.effective_api_key == "test_token_12345"

    s2 = Settings(api_key="sk-test-key")
    assert s2.effective_api_key == "sk-test-key"

    s3 = Settings()
    assert s3.effective_api_key is None


def test_helpers_base64_and_hex():
    """测试 Base64 编解码与十六进制生成。"""
    raw_str = "Duck2API Playwright Engine 测试"
    encoded = b64_encode(raw_str)
    decoded = b64_decode(encoded)
    assert decoded == raw_str

    hex_str = random_hex(16)
    assert len(hex_str) == 32

    hash_val = sha256_hash("hello")
    assert len(hash_val) == 64
    assert hash_val == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"

    assert current_timestamp_ms() > 0
    assert current_timestamp_s() > 0


def test_token_counter():
    """测试 Token 数量估算。"""
    # 纯英文估算
    eng_tokens = count_tokens("Hello world from Duck2API")
    assert eng_tokens > 0

    # 包含中文字符估算
    cn_tokens = count_tokens("你好，世界！这是一段中文测试")
    assert cn_tokens >= 10

    # 消息列表估算
    messages = [
        {"role": "user", "content": "你好"},
        {"role": "assistant", "content": "你好！有什么我可以帮你的？"},
    ]
    total_tokens = count_messages_tokens(messages)
    assert total_tokens > 10

    # 哈希计算
    prompt_h = hash_prompt("测试提示词")
    assert len(prompt_h) == 16
