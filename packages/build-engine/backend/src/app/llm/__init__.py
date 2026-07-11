"""LLM Provider — 系统级 AI 能力抽象层。

支持多种后端（DeepSeek / OpenAI / 自定义），
为对话 Agent、翻译、文档生成等场景提供统一调用接口。
"""

from .provider import get_llm_provider, LLMProvider, DeepSeekProvider
from .translation import translate_change_name, is_valid_kebab_case

__all__ = [
    "get_llm_provider", "LLMProvider", "DeepSeekProvider",
    "translate_change_name", "is_valid_kebab_case",
]
