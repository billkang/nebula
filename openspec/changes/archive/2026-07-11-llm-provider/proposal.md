## Why

星云平台的对话 Agent、change_name 翻译、后续的文档生成等场景都需要调用 LLM，但目前系统**没有任何 LLM API 的接入能力**：

- `langchain-openai` 依赖虽然存在，但从未被导入或使用
- LangGraph Agent 是纯规则驱动的，所有回复都是硬编码的模板消息
- ProjectService 创建项目时没有 LLM 翻译能力
- 每个需要 LLM 的场景都得自己实现 HTTP 调用，重复造轮子

需要一个统一的、可扩展的 LLM Provider 抽象层，让系统各模块能以一致的方式调用 AI 能力。

## What Changes

1. **新增 `app/llm/` 包** — 系统级 LLM 抽象层，包含 Provider 接口和实现
2. **新增 `LLMProvider` 抽象基类** — 定义 `chat()` 和 `chat_stream()` 核心方法
3. **新增 `DeepSeekProvider` 实现** — 基于 OpenAI 兼容 API，接入 DeepSeek
4. **新增 `OpenAIClientProvider` 通用实现** — 支持其他 OpenAI 兼容 API（预留）
5. **配置系统扩展** — 增加 `llm_provider`、`llm_model`、`DEEPSEEK_API_KEY`、`llm_base_url` 等配置项
6. **新增 `openai` 依赖** — 轻量 SDK，DeepSeek API 兼容
7. **保留 `langchain-openai` 依赖** — LangGraph 未来可能需要直接调用 LLM，但 Provider 层不依赖它
8. **集成到 ProjectService** — 创建项目时用 LLM 翻译 change_name

## Capabilities

### New Capabilities
- `llm-provider`: 系统级 LLM Provider 抽象层，提供统一的 chat/chat_stream 接口、配置管理和 Provider 注册

### Modified Capabilities
<!-- No existing capability requirements change — this is a new infrastructure layer -->

## Impact

- **新依赖**: `openai>=1.0.0`（已添加到 `pyproject.toml`）
- **配置**: `.env` 新增 `DEEPSEEK_API_KEY`、`LLM_MODEL` 等
- **新模块**: `src/app/llm/` 包（provider.py、`__init__.py`）
- **已有代码**: `ProjectService.create_project` 接入 LLM 翻译（首次 change_name 生成）
- **不修改**: 已有模型的表结构、API 路由签名、前端代码
