"""Change name 翻译功能测试（TDD）。

测试计划：
1. translate_change_name 成功返回 kebab-case
2. 校验函数 reject 非法格式
3. 校验函数 accept 合法格式
4. LLM 返回非法格式时重试
5. 重试后仍非法则抛异常
6. system prompt 包含规则说明
"""

from unittest.mock import MagicMock

import pytest

from app.llm import LLMProvider


def _make_mock_provider(return_value=None, side_effect=None):
    """创建一个 mock LLMProvider，chat() 返回指定值。"""
    provider = MagicMock(spec=LLMProvider)
    if side_effect is not None:
        provider.chat.side_effect = side_effect
    else:
        provider.chat.return_value = return_value
    return provider


# ===== 第一步：成功翻译 =====

def test_translate_change_name_chinese():
    """中文项目名翻译为 kebab-case。

    "旅游助手" → "travel-assistant"
    """
    from app.llm.translation import translate_change_name

    provider = _make_mock_provider(return_value="travel-assistant")
    result = translate_change_name("旅游助手", provider=provider)
    assert result == "travel-assistant"


def test_translate_change_name_english():
    """英文项目名保持 kebab-case。

    "E-commerce Dashboard" → "e-commerce-dashboard"
    """
    from app.llm.translation import translate_change_name

    provider = _make_mock_provider(return_value="e-commerce-dashboard")
    result = translate_change_name("E-commerce Dashboard", provider=provider)
    assert result == "e-commerce-dashboard"


# ===== 第二步：校验函数 =====

def test_is_valid_kebab_case_valid():
    from app.llm.translation import is_valid_kebab_case
    assert is_valid_kebab_case("travel-assistant")
    assert is_valid_kebab_case("my-project-123")
    assert is_valid_kebab_case("a")
    assert is_valid_kebab_case("hello-world")


def test_is_valid_kebab_case_invalid():
    from app.llm.translation import is_valid_kebab_case
    assert not is_valid_kebab_case("Travel-Assistant")  # 大写
    assert not is_valid_kebab_case("travel assistant")  # 空格
    assert not is_valid_kebab_case("travel_assistant")  # 下划线
    assert not is_valid_kebab_case("-travel")            # 前导-
    assert not is_valid_kebab_case("travel-")            # 尾随-
    assert not is_valid_kebab_case("")                   # 空
    assert not is_valid_kebab_case("travel--assistant")  # 连续--
    assert not is_valid_kebab_case("旅游助手")            # 中文


# ===== 第三步：重试逻辑 =====

def test_translate_retry_on_invalid():
    """LLM 首次返回非法格式，重试后成功。"""
    from app.llm.translation import translate_change_name

    provider = _make_mock_provider(side_effect=["Travel-Assistant", "travel-assistant"])
    result = translate_change_name("旅游助手", provider=provider)
    assert result == "travel-assistant"
    assert provider.chat.call_count == 2


def test_translate_fails_after_retries():
    """重试耗尽后仍非法，抛出 ValueError。"""
    from app.llm.translation import translate_change_name

    provider = _make_mock_provider(return_value="Invalid Name")
    with pytest.raises(ValueError, match="翻译结果不合法"):
        translate_change_name("测试项目", provider=provider)


def test_translate_empty_llm_response():
    """LLM 返回空字符串视为非法。"""
    from app.llm.translation import translate_change_name

    provider = _make_mock_provider(return_value="")
    with pytest.raises(ValueError, match="翻译结果不合法"):
        translate_change_name("测试项目", provider=provider)


# ===== 第四步：集成场景 =====

def test_translate_system_prompt_includes_rules():
    """翻译调用应传 system prompt 说明规则。"""
    from app.llm.translation import translate_change_name

    provider = _make_mock_provider(return_value="my-project")
    translate_change_name("我的项目", provider=provider)

    # 验证传入了 system prompt
    call_args = provider.chat.call_args
    assert call_args is not None
    sys_prompt = call_args[1].get("system_prompt", "")
    assert "kebab-case" in sys_prompt.lower()
    assert "pinyin" in sys_prompt.lower()
