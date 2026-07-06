## Context

星云（Nebula）是一个面向产品经理的 AI Agent 中台平台。MVP v1 的核心目标是跑通"PM 提需求 → 对话澄清 → 文档生成 → 编码执行 → 构建交付"的全链路，验证平台设想的可行性。

当前项目仅有脚手架代码（初始化 commit），无实际业务代码。后端基于 Python/FastAPI，前端基于 React/Vite/Tailwind，Agent 引擎使用 LangGraph。

### 当前状态

- 代码库已完成项目骨架初始化（目录结构、构建工具）
- 无用户系统、无项目管理、无对话 Agent、无编码调度能力
- 无数据库、无 API 服务

## Goals / Non-Goals

### Goals

- 实现可用的用户认证系统（注册、登录、JWT、内置用户）
- 实现多项目管理（创建、切换、隔离数据）
- 实现基于 LangGraph StateGraph 的五段式需求澄清对话流
- 集成 OpenSpec CLI 实现设计文档自动生成
- 实现本地 Claude Code 编码调度器
- 实现构建验证器（测试 + 打包）
- 实现匹配上述功能的 Web 界面（React + Tailwind）
- 提供简单的 RESTful API 支撑所有功能

### Non-Goals

- Docker 容器化编码执行（v1 本地运行）
- 运行时引擎 / 代码沙箱（nebula-runtime）
- Skill 匹配与推荐体系
- A2A / MCP Gateway
- 运维监控
- 多租户 / 细粒度权限控制
- OAuth / SSO 第三方登录
- OpenSpec 文档的自定义编辑（仅展示，不提供在线编辑）

## Decisions

### 1. 数据库选型：SQLite (v1) → PostgreSQL (上线前)

**决策：** v1 使用 SQLite 作为数据库，连接字符串抽为配置项，上线前切换到 PostgreSQL。

| 维度 | SQLite | 迁移 |
|------|--------|------|
| ORM | SQLAlchemy（屏蔽方言差异） | 换一行连接串 |
| 迁移 | Alembic（生成初始 migration） | 重新 autogenerate |
| 风险 | 不支持并发写入 → v1 无关 | 无 |

**迁移清单：**
- SQLite 特有约束（如 Boolean 存储差异）→ SQLAlchemy 已处理
- 连接串独立在 `.env` 文件中，不上传仓库

### 2. 认证方案：JWT + 中间件

**决策：** 使用 JWT（python-jose + passlib bcrypt）实现认证，FastAPI 中间件做鉴权。

- 简单、无状态、适合前后端分离
- 内置用户通过 seed 脚本初始化
- 新用户注册 → member 角色

### 3. 前后端分离

**决策：** v1 明确前后端分离架构。
- 后端：FastAPI 提供 REST API，端口 8000
- 前端：Vite React App 通过 fetch 调用 API，端口 5173（dev）/ 构建后由 FastAPI 静态文件服务托管
- 开发时跨域使用 Vite proxy 或 FastAPI CORS 中间件

### 4. Agent 实现：LangGraph StateGraph

**决策：** 使用 LangGraph 的 StateGraph 实现五段式对话状态机。

- 每段 Agent 行为由独立的 node 函数实现
- State 流转由条件路由控制
- 对话历史持久化到数据库
- v1 不考虑多轮对话的 context window 管理（对话不会太长）

### 5. 编码执行：subprocess 调用 Claude Code

**决策：** 通过 Python subprocess 调用本地 Claude Code CLI。

```python
subprocess.run(["claude", "code", "--prompt", instruction], cwd=project_dir)
```

- 不引入 Docker（v1 简化）
- 编码指令从 tasks.md 中提取
- 执行状态通过回调或轮询反馈给前端

### 6. OpenSpec 集成：subprocess 调用 CLI

**决策：** 通过 Python subprocess 调用 openspec CLI。

```python
subprocess.run(["openspec", "instructions", "proposal", "--change", change_name])
```

- 需求上下文从 Agent State 中提取，传入 proposal 生成
- 生成后的文档存储在 `openspec/changes/<change-name>/` 中

## Change Scope Matrix

| 模块 | 描述 | 前端 | 后端 | DB |
|------|------|------|------|-----|
| `user-auth` | 用户注册/登录、JWT 认证、内置用户、角色管理 | 登录页、注册页 | Auth API + JWT 中间件 | users 表 |
| `project-management` | 项目 CRUD、多项目切换、数据隔离 | 项目列表页 + 创建/删除 | Projects API + 权限校验 | projects 表 |
| `pm-chat-agent` | LangGraph 五段式对话流、状态管理、需求收集 | 对话页面 + 消息列表 | Chat API + Agent StateGraph | sessions + messages 表 |
| `doc-generation` | OpenSpec 文档生成触发与展示 | 文档概览页面 | Doc API + OpenSpec CLI 调用 | 文件系统 |
| `coding-executor` | 本地 Claude Code 调度、编码执行 | 编码状态展示 | Executor API + subprocess | 文件系统 |
| `build-verifier` | 测试运行、完整性校验、Artifact 打包 | 构建状态展示 | Builder API + 脚本 | artifact 元数据 |

## API Contract

### 通用规范

- 基础路径：`/api/v1`
- 认证方式：`Authorization: Bearer <token>`
- 响应格式：`{"data": {}, "error": null}` 或 `{"data": null, "error": "message"}`
- CORS：开发环境允许 `localhost:5173`

### Auth API

```
POST   /api/v1/auth/register        # 注册
POST   /api/v1/auth/login           # 登录，返回 JWT
GET    /api/v1/auth/me              # 获取当前用户信息
```

### Projects API

```
GET    /api/v1/projects             # 项目列表
POST   /api/v1/projects             # 创建项目
GET    /api/v1/projects/:id         # 项目详情
DELETE /api/v1/projects/:id         # 删除项目
```

### Chat API

```
GET    /api/v1/projects/:id/sessions     # 会话列表
POST   /api/v1/projects/:id/sessions     # 创建会话
GET    /api/v1/projects/:id/sessions/:sid # 会话消息
POST   /api/v1/projects/:id/sessions/:sid/messages  # 发送消息 → Agent 处理
```

### Documents API

```
GET    /api/v1/projects/:id/docs         # 文档列表
GET    /api/v1/projects/:id/docs/:type   # 文档详情（proposal/specs/design/tasks）
POST   /api/v1/projects/:id/docs/generate  # 触发 OpenSpec 文档生成
```

### Executor API

```
POST   /api/v1/projects/:id/execute      # 触发编码执行
GET    /api/v1/projects/:id/execute/status # 编码执行状态
```

### Build API

```
POST   /api/v1/projects/:id/build        # 触发构建验证
GET    /api/v1/projects/:id/build/status  # 构建状态
GET    /api/v1/projects/:id/artifacts     # Artifact 列表
```

## Data Model

### DB Tables

**users**
```
id          UUID    PK
username    TEXT    UNIQUE
email       TEXT    UNIQUE
password    TEXT    hashed
role        TEXT    "admin" | "member"
created_at  DATETIME
```

**projects**
```
id          UUID    PK
name        TEXT
description TEXT
owner_id    UUID    FK → users.id
created_at  DATETIME
updated_at  DATETIME
```

**sessions**
```
id          UUID    PK
project_id  UUID    FK → projects.id
status      TEXT    "active" | "completed"
created_at  DATETIME
updated_at  DATETIME
```

**messages**
```
id          UUID    PK
session_id  UUID    FK → sessions.id
role        TEXT    "user" | "agent"
content     TEXT
phase       TEXT    NULL (仅 agent 消息标注状态: greeting/collecting/clarifying/confirming)
created_at  DATETIME
```

### 文件系统结构

```
projects/<project-id>/
  ├── src/                        ← 生成的业务源码
  ├── requirements.txt            ← 依赖声明
  ├── Dockerfile                  ← 运行镜像定义
  ├── manifest.json               ← 版本号、入口、依赖
  └── artifacts/
      └── v1/                     ← Build Artifact 版本目录
          └── (tar 包)

openspec/changes/mvp-scope-planning/
  ├── proposal.md
  ├── specs/
  │   ├── user-auth/spec.md
  │   ├── project-management/spec.md
  │   ├── pm-chat-agent/spec.md
  │   ├── doc-generation/spec.md
  │   ├── coding-executor/spec.md
  │   └── build-verifier/spec.md
  ├── design.md
  └── tasks.md
```

## Frontend Architecture

### 页面路由

```
/login              → 登录页
/register           → 注册页
/projects           → 项目列表页（受保护）
/projects/:id       → 项目对话页（受保护）
/projects/:id/docs  → 文档展示页（受保护）
```

### 组件树（简化）

```
App
├── AuthLayout (登录/注册)
│   ├── LoginForm
│   └── RegisterForm
└── AppLayout (受保护)
    ├── Sidebar (项目列表 / 切换)
    ├── ChatArea
    │   ├── MessageList
    │   ├── MessageBubble (用户 / Agent)
    │   ├── ConfirmCard (确认范围卡片)
    │   └── MessageInput
    └── DocPanel
        ├── DocOverview
        └── DocViewer
```

### 状态管理

- **zustand**: 全局状态（用户信息、当前项目）
- **@tanstack/react-query**: 服务端数据获取（API 调用缓存 + 自动刷新）

## Backend Architecture

### 项目结构

```
backend/
  ├── app/
  │   ├── main.py            ← FastAPI 应用入口
  │   ├── config.py          ← 配置管理（.env）
  │   ├── database.py        ← SQLAlchemy engine + session
  │   ├── models/            ← SQLAlchemy 数据模型
  │   │   ├── __init__.py
  │   │   ├── user.py
  │   │   ├── project.py
  │   │   ├── session.py
  │   │   └── message.py
  │   ├── api/               ← 路由
  │   │   ├── __init__.py
  │   │   ├── auth.py
  │   │   ├── projects.py
  │   │   ├── chat.py
  │   │   ├── documents.py
  │   │   ├── executor.py
  │   │   └── build.py
  │   ├── services/          ← 业务逻辑
  │   │   ├── __init__.py
  │   │   ├── auth_service.py
  │   │   ├── project_service.py
  │   │   ├── chat_service.py
  │   │   ├── doc_service.py
  │   │   ├── executor_service.py
  │   │   └── build_service.py
  │   ├── agent/             ← LangGraph Agent
  │   │   ├── __init__.py
  │   │   ├── graph.py       ← StateGraph 定义
  │   │   ├── nodes.py       ← 各阶段 node 函数
  │   │   └── state.py       ← ChatState TypedDict
  │   └── middleware/
  │       ├── __init__.py
  │       └── auth.py        ← JWT 认证中间件
  ├── tests/
  ├── alembic/               ← 数据库迁移
  ├── requirements.txt
  ├── Dockerfile
  └── .env.example
```

### 依赖清单

```
fastapi
uvicorn
sqlalchemy
alembic
python-jose[cryptography]
passlib[bcrypt]
pydantic
pydantic-settings
python-multipart
langgraph
langchain-openai    # LangGraph 底层 LLM 调用
httpx               # 异步 HTTP 客户端
```

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| LangGraph 引入额外复杂度，而 v1 对话逻辑简单 | v1 仅使用 StateGraph 基础能力，不引入 LangGraph Cloud / LangSmith 等重量级组件 |
| SQLite 不适合生产环境，迁移到 PostgreSQL 可能有坑 | 连接串抽配置项，上线前做全量功能测试验证 |
| 本地 Claude Code 调用依赖用户环境 | 编码前做前置检查（claude --version），失败时给出安装指引 |
| OpenSpec CLI 的输出格式变化可能导致解析失败 | 前端展示原始 Markdown + 容错降级 |
| JWT 无状态，无法主动失效 | v1 允许短有效期（24h，平衡安全与易用——太短影响体验，太长不安全）+ 前端登出时清除本地 token。v1 不做 refresh token，到期重新登录 |
| 多项目对话数据量大时查询性能 | v1 用户数少，不会出现性能问题 |
