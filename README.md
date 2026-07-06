# 星云 · Nebula

> **星云深处，万物始生。**
> *Where stars are born.*

**星云 (Nebula)** 是 AI Agent 中台平台——把业务需求翻译成 Agent 开发指令，调度成熟工具完成交付。

---

## 命名由来

星云（Nebula）是天文学中恒星的摇篮——星际气体与尘埃在引力作用下凝聚、坍缩，最终诞生出新的恒星。

这与星云平台的使命完美对应：平台是"恒星孕育所"。项目需求就是星云中的原始物质，在平台的引力下凝聚成型，最终诞生出可独立运行的代码——一颗颗"恒星"。

---

## 核心定位

**AI Agent 中台** — 一个编排层平台。

- 🎯 **不造轮子** — 对接成熟方案（Claude Code 等），专注调度与编排
- 🎯 **中台之力** — 把业务集中，把人才聚集。所有 agent、skill、工具汇聚于此
- 🎯 **PM 驱动** — 产品经理是平台的一级用户，从需求到交付，无需写代码

---

## 架构概览

```mermaid
flowchart TB
    subgraph Client["客户端层"]
        React["React Web App"]
        SDK["API Client SDK"]
    end

    Client -->|HTTP / WebSocket| Gateway

    subgraph Gateway["API 网关层"]
        Auth["认证鉴权 · 路由 · 限流 · WS 管理"]
    end

    Gateway --> Platform

    subgraph Platform["平台层"]
        direction TB

        subgraph Engines["核心引擎"]
            direction LR
            subgraph Build["构建引擎"]
                B1["PM 对话 Agent"]
                B2["渐进式文档生成"]
                B3["Skill 匹配推荐"]
                B4["编码调度 (Docker)"]
            end
            subgraph Runtime["运行时引擎"]
                R1["LangGraph"]
                R2["MCP GW"]
                R3["A2A GW"]
                R4["监控日志"]
            end
        end

        subgraph Services["公共服务"]
            S1["Agent 管理 · Skill 管理 · 能力注册中心"]
        end
    end

    Platform --> DataLayer

    subgraph DataLayer["数据层"]
        PG[("PostgreSQL")]
        Redis[("Redis")]
        OSS[("对象存储")]
    end
```

### 构建引擎 (Build Engine)

PM 发起需求 → Build Session 贯穿始终：

1. **PM 对话 Agent** — 多轮对话逐步澄清需求（LangGraph StateGraph）
2. **渐进式文档生成** — 增量生成 PRD / 需求文档 / 架构设计 / 验收标准
3. **Skill 匹配** — 智能推荐适合场景的 Skill 模版
4. **编码调度** — Docker + Claude Code 自动完成开发

### 运行时引擎 (Runtime Engine)

Agent 部署后持续运行：

- **runtime-api** — 运行时 API / 对话触发
- **langgraph-cluster** — Agent 执行集群
- **mcp-gateway** — MCP 工具代理，连接外部工具
- **a2a-gateway** — Agent 间通信代理
- **agent-monitor** — 运行时监控 / 日志 / 告警

---

## 关键协议

| 协议 | 用途 | 位置 |
|------|------|------|
| **MCP** | 外部工具接入标准 | MCP Registry + MCP Gateway |
| **A2A** | Agent 间通信 | A2A Registry + A2A Gateway |

---

## 技术栈

| 层 | 技术 |
|------|------|
| 前端 | React |
| Agent 引擎 | LangGraph |
| 后端 | Python |
| 数据库 | PostgreSQL, Redis |
| 执行环境 | Docker (v1) → A2A (v2) |

---

## 快速开始

### 前置条件

- **Python 3.11+**（推荐 3.12）
- **Node.js 18+**（推荐 20 LTS）
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview)（编码执行器使用，可选）
- 包管理工具：`pip` + `npm`

### 第一步：启动后端

后端是 FastAPI 服务，提供 REST API。

```bash
# 1. 进入后端目录
cd backend

# 2. 配置环境变量
cp .env.example .env
# 编辑 .env 可修改数据库路径、JWT Secret、内置用户密码等

# 3. 安装依赖
pip install -r requirements.txt

# 4. 初始化数据库（建表 + 迁移）
alembic upgrade head

# 5. 初始化内置用户（admin / pm）
python seed.py

# 6. 启动开发服务器
uvicorn app.main:app --reload --port 8000
```

后端启动后，API 文档自动可用：
- Swagger UI：http://localhost:8000/docs
- ReDoc：http://localhost:8000/redoc

### 第二步：启动前端

```bash
# 1. 进入前端目录
cd frontend

# 2. 安装依赖
npm install

# 3. 启动开发服务器
npm run dev
```

前端开发服务器 → http://localhost:5173

### 访问平台

打开 http://localhost:5173 ，使用以下内置账号登录：

| 角色 | 用户名 | 密码 | 权限说明 |
|------|--------|------|---------|
| 管理员 | `admin` | `123456` | 全部权限（含删除项目） |
| 产品经理 | `pm` | `123456` | 使用平台，创建对话和项目 |

> 开发模式下，Vite 自动将 `/api/*` 请求代理到 `http://localhost:8000`，无需手动处理跨域。生产部署时，前端构建产物由 FastAPI 静态文件服务托管。

### 校验是否启动成功

```bash
# 终端 1 — 后端应输出类似：
# INFO:     Uvicorn running on http://127.0.0.1:8000

# 终端 2 — 前端应输出类似：
# VITE v5.x  ready in xxx ms
# ➜  Local:   http://localhost:5173/

# 测试 API 是否在线：
curl http://localhost:8000/api/v1/auth/me -H "Authorization: Bearer test" -w "\nHTTP %{http_code}"
# 应返回 401（未认证），说明服务正常
```

### 常见问题

| 问题 | 解决 |
|------|------|
| `alembic upgrade head` 报错 | 确保已在 `backend/` 目录下执行，且 `.env` 已创建 |
| `pip install` 卡住 | 尝试 `pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple`（国内镜像） |
| 前端请求后端 502 | 检查后端是否正在运行，端口 8000 未被占用 |
| `port 5173 already in use` | `npm run dev -- --port 5174` 使用其他端口 |
| SQLite 数据库位置 | 默认在 `backend/nebula.db`，可通过 `.env` 的 `DATABASE_URL` 修改 |

---

## 文档

- [平台架构设计](docs/agents/platform-architecture.md) — 完整架构文档
- [ADR 记录](docs/adr/) — 架构决策记录

---

## 愿景

> **让每个产品经理都拥有一支 Agent 军团。**
>
> 星云不造轮子，它让轮子转起来。当复杂的开发工作被结构化、标准化、自动化，产品经理将不再受制于开发排期。需求的尽头就是交付——这就是星云的力量。

---

<p align="center">⭐ 星云深处，万物始生 ⭐</p>
