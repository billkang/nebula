"""LLM Provider 抽象与实现。

支持 OpenAI 兼容 API（DeepSeek / OpenAI / 其他）。
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from openai import OpenAI

from app.config import settings

logger = logging.getLogger(__name__)


class LLMProvider(ABC):
    """LLM Provider 抽象基类。"""

    @abstractmethod
    def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """发送对话消息并返回文本响应。"""
        ...

    @abstractmethod
    def chat_stream(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        **kwargs: Any,
    ):
        """发送对话消息并流式返回响应片段。"""
        ...


class OpenAIClientProvider(LLMProvider):
    """基于 OpenAI SDK 的通用 Provider（兼容 DeepSeek / OpenAI / 等）。"""

    def __init__(
        self,
        api_key: str = "",
        base_url: str = "https://api.deepseek.com",
        model: str = "deepseek-chat",
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model
        logger.info(
            "LLM provider initialized: model=%s base_url=%s key_len=%d",
            self.model, self.base_url, len(self.api_key),
        )
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        **kwargs: Any,
    ) -> str:
        """发送对话并返回完整文本响应。"""
        params = self._build_params(messages, system_prompt, temperature, max_tokens, **kwargs)
        response = self._client.chat.completions.create(**params)
        return response.choices[0].message.content or ""

    def chat_stream(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        temperature: float = 0.3,
        max_tokens: int = 1024,
        **kwargs: Any,
    ):
        """发送对话并流式返回响应。"""
        params = self._build_params(messages, system_prompt, temperature, max_tokens, **kwargs)
        params["stream"] = True
        stream = self._client.chat.completions.create(**params)
        for chunk in stream:
            delta = chunk.choices[0].delta if chunk.choices else None
            if delta and delta.content:
                yield delta.content

    def _build_params(
        self,
        messages: list[dict],
        system_prompt: str | None,
        temperature: float,
        max_tokens: int,
        **kwargs: Any,
    ) -> dict:
        full_messages = list(messages)
        if system_prompt:
            full_messages.insert(0, {"role": "system", "content": system_prompt})
        return {
            "model": self.model,
            "messages": full_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            **kwargs,
        }


class DeepSeekProvider(OpenAIClientProvider):
    """DeepSeek 专用 Provider（默认配置）。"""

    def __init__(self, api_key: str = "", model: str = "deepseek-chat"):
        super().__init__(
            api_key=api_key,
            base_url="https://api.deepseek.com",
            model=model,
        )


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------

_PROVIDER: LLMProvider | None = None


def get_llm_provider() -> LLMProvider:
    """获取（或创建）全局 LLM Provider 单例。

    从 ``app.config.settings`` 读取 LLM 配置，按 ``llm_provider`` 字段选择后端。
    """
    global _PROVIDER
    if _PROVIDER is not None:
        return _PROVIDER

    provider_name = settings.llm_provider
    api_key = settings.llm_api_key
    model = settings.llm_model
    base_url = settings.llm_base_url

    if not api_key:
        raise RuntimeError(
            "LLM API key 未配置。请在 .env 中设置 DEEPSEEK_API_KEY（或相应 provider 的 key）。"
        )

    if provider_name == "deepseek":
        _PROVIDER = DeepSeekProvider(api_key=api_key, model=model)
    else:
        _PROVIDER = OpenAIClientProvider(
            api_key=api_key,
            base_url=base_url,
            model=model,
        )

    return _PROVIDER


def reset_provider():
    """重置 Provider 单例（测试用）。"""
    global _PROVIDER
    _PROVIDER = None
