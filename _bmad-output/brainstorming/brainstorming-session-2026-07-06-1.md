# Brainstorming Session：Nebula MVP v1 范围定义

> 日期：2026-07-06
> 参与者：Bill、Claude
> Change：mvp-scope-planning

## 讨论主题

定义星云（Nebula）AI Agent 中台平台 MVP v1 的核心范围和技术方案。

## 项目背景

星云平台的核心定位是"给产品经理调度 Agent 军团的指挥台"——把业务需求翻译成 Agent 开发指令，调度成熟工具完成交付。不造轮子，不锁定客户。

## 关键决策

### v1 要做（核心链路）

| 组件 | 说明 |
|------|------|
| ① LangGraph 对话 Agent | 简单 StateGraph 对话流，用于需求澄清 |
| ② OpenSpec 文档生成 | 直接复用 OpenSpec CLI，不自研 |
| ③ 编码调度器 | 本地运行 Claude Code，不 Docker 化 |
| ④ 构建验证器 | 测试 + 打包 → Build Artifact |
| ⑤ Web 界面 | 匹配上述功能的轻度前端 |
| ⑥ 用户系统 | JWT 认证，内置用户 + 注册功能 |
| ⑦ 多项目管理 | 支持创建多个项目，分别对话 |

### 技术栈

| 层 | 技术 |
|------|------|
| 前端 | React + TypeScript + Vite + Tailwind |
| 后端 | Python + FastAPI |
| Agent 引擎 | LangGraph（简单 StateGraph 对话流） |
| 数据库 | SQLite（v1）→ PostgreSQL（上线前适配） |
| ORM | SQLAlchemy + Alembic |
| 认证 | Session/JWT |
| 文档生成 | OpenSpec CLI |
| 编码执行 | 本地 Claude Code |
| 构建 | pytest + 脚本打包 |

### 明确不做的（v1 红线）

- Docker 容器化编码执行
- 运行时引擎（nebula-runtime）与代码沙箱
- Skill 体系（Skill 匹配与推荐）
- A2A Gateway（Agent 间通信）
- MCP Gateway（外部工具代理）
- 运维监控
- 多租户 / 权限细粒度控制
- OAuth / SSO 第三方登录

### 数据库策略

v1 先用 SQLite 加速开发，数据库连接串抽成配置项。上线前迁移到 PostgreSQL，利用 SQLAlchemy + Alembic 的迁移能力，预期迁移成本低。

## 需求要点

1. 用户登录后看到项目列表，可选择或创建项目
2. 进入项目后进入对话界面，与 LangGraph Agent 对话澄清需求
3. 对话收敛后，调用 OpenSpec 生成设计文档（proposal → specs → design → tasks）
4. 平台调度本地 Claude Code 执行编码
5. 编码完成后运行测试 + 打包为 Build Artifact
6. 整个流程在 Web 界面中有基本的进度展示

## 边界范围

- v1 聚焦"跑通链路"，不追求功能完整度
- 每个组件能做到"有用"即可，不要求完善
- 编码执行层面先通过本地 Claude Code 验证设想，后续再 Docker 化

## 后续步骤

1. → openspec SDD 文档生成（proposal → specs → design → tasks）
2. spec-hardener 审查
3. writing-plans 生成实现计划
4. 用户确认后进入 TDD 实现
