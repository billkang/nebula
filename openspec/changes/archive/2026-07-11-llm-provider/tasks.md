## 1. 依赖与配置

- [x] 1.1 确认 `openai>=1.0.0` 已添加到 `pyproject.toml`（✅ 已添加）
- [x] 1.2 确认 `Settings` 已扩展 LLM 配置字段（✅ 已添加）
- [x] 1.3 运行 `uv sync` 安装新依赖（❌ 网络不可达，但 `openai` 已预装在系统中）
- [x] 1.4 确认 `.env.example` 已更新 `DEEPSEEK_API_KEY`/`LLM_MODEL`（✅ 已更新）

## 2. LLM Provider 核心

- [x] 2.1 创建 `app/llm/` 包结构（✅ 已创建）
- [x] 2.2 实现 `LLMProvider` 抽象基类（chat / chat_stream）（✅ 已实现）
- [x] 2.3 实现 `OpenAIClientProvider` 通用实现（✅ 已实现）
- [x] 2.4 实现 `DeepSeekProvider`（继承 OpenAIClientProvider）（✅ 已实现）
- [x] 2.5 实现 `get_llm_provider()` 工厂函数 + 单例 + `reset_provider()`（✅ 已实现）

## 3. 翻译集成

- [x] 3.1 在 `ProjectService` 中接入 LLM 翻译 change_name
- [x] 3.2 实现翻译结果校验（kebab-case 正则）
- [x] 3.3 实现翻译失败重试逻辑
- [x] 3.4 更新 `ProjectService.create_project` 返回含 change_name

## 4. 测试

- [x] 4.1 编写 LLM Provider 单元测试（mock API 调用）
- [x] 4.2 编写 change_name 翻译逻辑测试
- [x] 4.3 运行测试验证全部通过（132/132）
