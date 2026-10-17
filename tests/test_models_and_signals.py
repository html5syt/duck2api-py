"""模型映射与前端轨迹信号测试。"""

import json
from duck2api.core.models import ModelRegistry
from duck2api.core.signals import SignalGenerator
from duck2api.utils.helpers import b64_decode


def test_model_alias_resolution():
    """测试常见模型别名解析。"""
    assert ModelRegistry.resolve_model("gpt-4o-mini") == "gpt-5.4-mini"
    assert ModelRegistry.resolve_model("gpt-4o") == "gpt-6-luna"
    assert ModelRegistry.resolve_model("gpt-3.5-turbo") == "gpt-5.4-mini"
    assert ModelRegistry.resolve_model("claude-3-haiku") == "claude-haiku-4-5"
    assert ModelRegistry.resolve_model("mistral-small") == "mistral-small-2603"
    assert ModelRegistry.resolve_model("custom-model-id") == "custom-model-id"


def test_reasoning_effort_mapping():
    """测试推理级别限制映射。"""
    assert ModelRegistry.map_reasoning_effort("none") == "none"
    assert ModelRegistry.map_reasoning_effort(None) == "none"
    assert ModelRegistry.map_reasoning_effort("") == "none"
    assert ModelRegistry.map_reasoning_effort("low") == "low"
    assert ModelRegistry.map_reasoning_effort("medium") == "low"
    assert ModelRegistry.map_reasoning_effort("high") == "low"
    assert ModelRegistry.map_reasoning_effort("max") == "low"


def test_fe_signals_generation():
    """测试行为遥测信号生成格式及合法性。"""
    signals_b64 = SignalGenerator.create_fe_signals()
    assert isinstance(signals_b64, str)
    assert len(signals_b64) > 0

    decoded_json = b64_decode(signals_b64)
    data = json.loads(decoded_json)

    assert "start" in data
    assert "events" in data
    assert "end" in data
    assert isinstance(data["events"], list)
    assert len(data["events"]) >= 4

    event_names = [e["name"] for e in data["events"]]
    assert "onboarding_impression" in event_names
    assert "action" in event_names
    assert "onboarding_finish" in event_names
    assert "startNewChat_free" in event_names


def test_journey_id_generation():
    """测试 32 字符十六进制会话 ID。"""
    jid = SignalGenerator.generate_journey_id()
    assert isinstance(jid, str)
    assert len(jid) == 32
