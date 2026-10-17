"""前端信号与行为模拟模块。

负责生成与真实用户一致的前端轨迹信号 (x-fe-signals) 及会话追踪 ID (x-ddg-journey-id)。
"""

import base64
import json
import random
import secrets
import time
from typing import Dict, Any


class SignalGenerator:
    """前端行为遥测信号生成器。"""

    @staticmethod
    def generate_journey_id() -> str:
        """生成 32 字符的十六进制追踪 ID。"""
        return secrets.token_hex(16)

    @staticmethod
    def create_fe_signals() -> str:
        """构造模拟用户真实交互流程的 x-fe-signals 负载。

        包含 onboarding_impression -> action -> onboarding_finish -> startNewChat_free。
        """
        now = int(time.time() * 1000)

        # 模拟自然时延
        impression = random.randint(50, 150)
        action = impression + random.randint(3000, 12000)
        finish = action + random.randint(800, 3000)
        start_chat = finish + random.randint(20, 120)
        end = start_chat + random.randint(2, 10)

        payload: Dict[str, Any] = {
            "start": now - end,
            "events": [
                {"name": "onboarding_impression", "delta": impression},
                {"name": "action", "delta": action, "trusted": True},
                {"name": "onboarding_finish", "delta": finish},
                {"name": "startNewChat_free", "delta": start_chat},
            ],
            "end": end,
        }

        encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
        return encoded
