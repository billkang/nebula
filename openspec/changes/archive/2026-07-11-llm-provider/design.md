## Context

星云平台目前没有任何直接 LLM API 的接入能力：

- **LangGraph Agent**（`app/agent/nodes.py`）纯规则驱动，所有回复是硬编码模板 — 没有真正调用过 LLM
- **依赖**：`langchain-openai` 在 `pyproject.toml` 中但从未被导入或使用
- **唯一 AI 集成**：Docker 内的 Claude Code CLI（编码执行器），走 subprocess 而非 API 调用
- **配置系统**：无 `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` 类变量

需求场景：
1. **近期**：项目创建时的中文名→英文 kebab-case 翻译（`ProjectService.create_project`）
2. **近期**：PM 对话 Agent 从模板回复升级为 LLM 驱动
3. **远期**：文档生成、需求分析、Skill 匹配等

需要一个系统级、可扩展的 LLM 抽象层，避免每个场景各自实现 HTTP 调用。

## Goals / Non-Goals

**Goals:**
- 提供统一的 `chat()` 和 `chat_stream()` 接口，屏蔽不同 Provider 的 API 差异
- 接入 DeepSeek 作为首个 LLM 后端
- 支持通过配置切换 Provider（DeepSeek ↔ OpenAI ↔ 自定义）
- 全局单例管理 LLM 客户端，避免重复创建连接
- 集成到 ProjectService 的 change_name 翻译

**Non-Goals:**
- 不做 LangGraph Agent 的 LLM 驱动改造（留待后续 change `agent-llm-integration`）
- 不做流式对话的 SSE 推送（留待后续 change）
- 不做 Prompt 管理/版本化（后续再考虑）

## Decisions

### 1. Provider 抽象 — 接口 vs 直接调用

| 选项 | 结论 |
|------|------|
| 抽象基类 `LLMProvider` + 多实现 | ✅ 选 |
| 直接在各处调用 `openai.OpenAI` | ❌ 耦合 Provider，切换成本高 |

抽象层让切换 Provider 只需改配置，不影响已有调用方。

### 2. SDK 选型 — `openai` vs `langchain-openai`

| 维度 | `openai` SDK | `langchain-openai` |
|------|-------------|-------------------|
| 依赖大小 | 轻量（~200KB） | 较重（~2MB + langchain-core） |
| API 兼容 | DeepSeek 兼容 | 通过 LCEL 封装 |
| 使用复杂度 | 直接 | 需理解 LangChain 抽象 |
| 已有依赖 | ❌ 新加 | ✅ 已存在但未使用 |

**选 `openai` SDK。** 理由：
- DeepSeek API 完全兼容 OpenAI 格式，改 `base_url` 即可
- 更轻量、更直接，没有 LangChain 的抽象开销
- `langchain-openai` 保留不动，LangGraph 未来如需直接调用 LLM 时可复用

### 3. Provider 模式 — 单例 vs 每次新建

| 选项 | 结论 |
|------|------|
| 工厂函数 + 全局单例 | ✅ 选 |
| 每次调用新建 client | ❌ 重复建立连接，浪费 |

LLM client 内部维护连接池，复用减少握手开销。支持测试时调用 `reset_provider()` 重置。

### 4. 配置方式 — pydantic-settings

扩展现有的 `Settings` 类（`app/config.py`），新增 4 个字段。`DEEPSEEK_API_KEY` 从 `.env` 加载。

### 5. DeepSeek 模型选型

| 模型 | 用途 |
|------|------|
| `deepseek-chat` | 对话、翻译（默认） |
| `deepseek-reasoner` | 推理任务（预留） |

初始使用 `deepseek-chat`，性价比高，中英文都支持。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| DeepSeek API 不稳定或延迟高 | Provider 抽象层支持快速切换到 OpenAI/其他 |
| API Key 泄露 | 从 `.env` 文件加载，不硬编码；后续可对接密钥管理服务 |
| LLM 翻译结果不符合 kebab-case | System Prompt 给出明确规则 + 示例，调用后做正则校验，不合规重试 |
| 单例在测试环境中状态残留 | 提供 `reset_provider()` 方法，测试用例中可重置 |
