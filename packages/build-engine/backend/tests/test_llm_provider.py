"""LLM Provider 单元测试。

测试策略：mock OpenAI client，不发起真实 API 调用。
"""

from unittest.mock import MagicMock, patch

import pytest

from app.llm import LLMProvider, DeepSeekProvider, get_llm_provider
from app.llm.provider import OpenAIClientProvider, reset_provider


def test_llm_provider_abstract_cannot_instantiate():
    """LLMProvider 是抽象基类，不能直接实例化。"""
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore


def test_deepseek_provider_defaults():
    """DeepSeekProvider 使用默认 base_url 和 model。"""
    p = DeepSeekProvider(api_key="sk-test")
    assert p.base_url == "https://api.deepseek.com"
    assert p.model == "deepseek-chat"


def test_openai_client_provider_custom_config():
    """OpenAIClientProvider 支持自定义 base_url 和 model。"""
    p = OpenAIClientProvider(
        api_key="sk-test",
        base_url="https://custom.api.com/v1",
        model="custom-model",
    )
    assert p.base_url == "https://custom.api.com/v1"
    assert p.model == "custom-model"


class TestBuildParams:
    """_build_params 参数组装逻辑。"""

    def test_build_params_basic(self):
        p = OpenAIClientProvider(api_key="sk-test")
        params = p._build_params(
            messages=[{"role": "user", "content": "Hello"}],
            system_prompt=None,
            temperature=0.3,
            max_tokens=1024,
        )
        assert params["model"] == "deepseek-chat"
        assert params["messages"] == [{"role": "user", "content": "Hello"}]
        assert params["temperature"] == 0.3
        assert params["max_tokens"] == 1024

    def test_build_params_with_system_prompt(self):
        p = OpenAIClientProvider(api_key="sk-test")
        params = p._build_params(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt="You are a translator",
            temperature=0.5,
            max_tokens=256,
        )
        # system prompt 插到 messages 最前面
        assert params["messages"] == [
            {"role": "system", "content": "You are a translator"},
            {"role": "user", "content": "Hi"},
        ]
        assert params["temperature"] == 0.5
        assert params["max_tokens"] == 256

    def test_build_params_extra_kwargs(self):
        p = OpenAIClientProvider(api_key="sk-test")
        params = p._build_params(
            messages=[{"role": "user", "content": "Hi"}],
            system_prompt=None,
            temperature=0.3,
            max_tokens=512,
            top_p=0.9,
            presence_penalty=0.1,
        )
        # 额外参数透传
        assert params["top_p"] == 0.9
        assert params["presence_penalty"] == 0.1


class TestChat:
    """chat() 方法测试（mock OpenAI API）。"""

    @patch("app.llm.provider.OpenAI")
    def test_chat_returns_content(self, mock_openai):
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="Hello back!"))]
        )

        p = OpenAIClientProvider(api_key="sk-test")
        result = p.chat([{"role": "user", "content": "Hi"}])

        assert result == "Hello back!"

    @patch("app.llm.provider.OpenAI")
    def test_chat_empty_content_returns_empty_string(self, mock_openai):
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content=None))]
        )

        p = OpenAIClientProvider(api_key="sk-test")
        result = p.chat([{"role": "user", "content": "Hi"}])

        assert result == ""

    @patch("app.llm.provider.OpenAI")
    def test_chat_passes_system_prompt(self, mock_openai):
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance
        mock_instance.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content="OK"))]
        )

        p = OpenAIClientProvider(api_key="sk-test")
        p.chat(
            [{"role": "user", "content": "翻译：你好"}],
            system_prompt="You are a translator",
        )

        # 验证系统 prompt 传给了 API
        call_kwargs = mock_instance.chat.completions.create.call_args[1]
        messages = call_kwargs["messages"]
        assert messages[0] == {"role": "system", "content": "You are a translator"}


class TestChatStream:
    """chat_stream() 方法测试（mock OpenAI API）。"""

    @patch("app.llm.provider.OpenAI")
    def test_chat_stream_yields_chunks(self, mock_openai):
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance

        # 模拟流式返回两个 chunk
        chunk1 = MagicMock()
        chunk1.choices = [MagicMock(delta=MagicMock(content="Hello "))]
        chunk2 = MagicMock()
        chunk2.choices = [MagicMock(delta=MagicMock(content="world!"))]
        mock_instance.chat.completions.create.return_value = [chunk1, chunk2]

        p = OpenAIClientProvider(api_key="sk-test")
        result = list(p.chat_stream([{"role": "user", "content": "Hi"}]))

        assert result == ["Hello ", "world!"]

    @patch("app.llm.provider.OpenAI")
    def test_chat_stream_skips_empty_chunks(self, mock_openai):
        mock_instance = MagicMock()
        mock_openai.return_value = mock_instance

        chunk = MagicMock()
        chunk.choices = [MagicMock(delta=MagicMock(content=""))]
        mock_instance.chat.completions.create.return_value = [chunk]

        p = OpenAIClientProvider(api_key="sk-test")
        result = list(p.chat_stream([{"role": "user", "content": "Hi"}]))

        assert result == []


class TestFactory:
    """get_llm_provider() 工厂函数测试。"""

    def setup_method(self):
        reset_provider()

    @patch("app.llm.provider.settings")
    def test_get_llm_provider_deepseek(self, mock_settings):
        mock_settings.llm_provider = "deepseek"
        mock_settings.llm_api_key = "sk-deepseek"
        mock_settings.llm_model = "deepseek-chat"
        mock_settings.llm_base_url = "https://api.deepseek.com"

        provider = get_llm_provider()
        assert isinstance(provider, DeepSeekProvider)

    @patch("app.llm.provider.settings")
    def test_get_llm_provider_openai(self, mock_settings):
        mock_settings.llm_provider = "openai"
        mock_settings.llm_api_key = "sk-openai"
        mock_settings.llm_model = "gpt-4o"
        mock_settings.llm_base_url = "https://api.openai.com/v1"

        provider = get_llm_provider()
        assert isinstance(provider, OpenAIClientProvider)
        assert provider.base_url == "https://api.openai.com/v1"
        assert provider.model == "gpt-4o"

    @patch("app.llm.provider.settings")
    def test_get_llm_provider_singleton(self, mock_settings):
        mock_settings.llm_provider = "deepseek"
        mock_settings.llm_api_key = "sk-test"
        mock_settings.llm_model = "deepseek-chat"
        mock_settings.llm_base_url = "https://api.deepseek.com"

        p1 = get_llm_provider()
        p2 = get_llm_provider()
        assert p1 is p2  # 同一个实例

    @patch("app.llm.provider.settings")
    def test_get_llm_provider_no_api_key(self, mock_settings):
        mock_settings.llm_provider = "deepseek"
        mock_settings.llm_api_key = ""

        with pytest.raises(RuntimeError, match="API key 未配置"):
            get_llm_provider()

    def test_reset_provider(self):
        reset_provider()  # 正常工作，无异常
