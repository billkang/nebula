## Why

星云（Nebula）是一个面向产品经理的 AI Agent 中台平台，核心定位是"不造轮子"——把业务需求翻译成 Agent 开发指令，调度成熟工具完成交付。当前系统仅有脚手架代码（初始化 commit），需要定义并实现 MVP v1 的核心功能链路，验证平台设想是否成立。

## What Changes

- 创建完整的 Web 应用框架（React 前端 + FastAPI 后端）
- 实现用户系统（注册、登录、JWT 认证，内置 admin/pm 用户）
- 实现多项目管理能力（创建项目、切换项目、分别对话）
- 引入 LangGraph 实现简单对话 Agent（需求澄清对话流）
- 集成 OpenSpec CLI 实现设计文档自动生成（proposal → specs → design → tasks）
- 实现本地 Claude Code 编码调度器（执行 OpenSpec 生成的编码任务）
- 实现构建验证器（运行测试、打包为 Build Artifact）
- **明确不做的**：Docker 容器化编码、运行时引擎、代码沙箱、Skill 体系、A2A/MCP Gateway、运维监控

## Capabilities

### New Capabilities
- `user-auth`: 用户注册、登录、JWT 认证，内置用户角色（admin/pm）
- `project-management`: 项目 CRUD，多项目分别对话
- `pm-chat-agent`: 基于 LangGraph StateGraph 的需求澄清对话流
- `doc-generation`: 集成 OpenSpec CLI 生成设计文档（proposal/specs/design/tasks）
- `coding-executor`: 本地 Claude Code 编码调度与执行
- `build-verifier`: 测试运行 + Build Artifact 打包

### Modified Capabilities

无（新项目，无既有规格需要修改）

## Impact

- **新项目**：从零开始搭建，无既有代码迁移
- **依赖新增**：LangGraph、FastAPI、SQLAlchemy、Alembic、React、Vite、Tailwind、OpenSpec CLI
- **运行环境**：需要 Python 3.11+、Node.js 18+、本地 Claude Code 可用
- **不存在兼容性风险**（全新项目起点）

## Out of Scope

| 项目 | 说明 | 归属 |
|------|------|------|
| Docker 容器化编码执行 | v1 本地 subprocess 调用 Claude Code，不做容器编排 | v2 规划 |
| 运行时引擎（nebula-runtime） | 客户侧运行平台，v1 只产代码不提供运行环境 | v2+ |
| 代码沙箱（在线运行/编辑） | 差异化亮点但工程量大，v1 不做 | v2+ |
| Skill 体系（匹配与推荐） | 需要积累模板库才有意义，v1 手动指定 | v2+ |
| A2A/MCP Gateway | Agent 通信和外部工具代理，v1 无需求 | v2+ |
| 运维监控 | 平台自身及 Agent 运行时监控 | v2+ |
| OAuth / SSO / 第三方登录 | v1 仅邮箱密码注册 | v2 |
| 多租户 / 细粒度权限 | v1 仅两级角色（admin/member） | v2 |
| 联并发支持（>10 用户同时使用） | SQLite 不擅长并发写入 | 上线前切换 PG 后 |

## Known Limitations

- **LangGraph API 稳定性**：LangGraph 仍处于快速迭代期，v1 仅使用其 StateGraph 基础能力，避免绑定高级功能。后续版本升级时需关注 API 兼容性。
- **本地 Claude Code 环境依赖**：星云平台依赖用户本地安装 Claude Code CLI。Claude Code 版本变化可能导致编码指令格式需要适配。
- **SQLite → PostgreSQL 迁移**：SQLAlchemy 屏蔽了大部分差异，但 SQLite 不支持 PostgreSQL 的部分高级特性（如原生 JSON 操作）。代码中应避免使用 PG 特有语法。
- **JWT 无刷新机制（v1 简化）**：v1 JWT 有效期 24h，无 refresh token。到期后用户需重新登录。后续版本可引入 refresh token 机制改善体验。
- **OpenSpec CLI 版本兼容性**：OpenSpec 版本升级可能改变 CLI 输出格式或参数。建议在 CI 中锁定 openspec 版本。
