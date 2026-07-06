## Context

Nebula 当前开发启动流程需手动执行 6 步以上操作（venv → 依赖 → 配置 → 迁移 → seed → 启动）。生产部署方面，builder/coder 已有 Docker 镜像，但 build-engine 缺少独立 Docker Compose。本设计覆盖本地开发（多平台）和生产部署（build-engine Docker Compose）两种场景。

当前项目结构（monorepo）：
- `packages/build-engine/backend/` — FastAPI 应用，SQLite，已对接 uv workspace
- `packages/build-engine/frontend/` — Vite + React，已对接 pnpm workspace
- `Makefile` — 已存在（dev/test/clean/build 入口）
- `scripts/start.sh` — 已存在（monorepo 路径，需要增强）
- `docker/` — 已包含 builder/coder Docker 配置

## Goals / Non-Goals

**Goals:**
- 增强 `scripts/start.sh`（macOS/Linux）/ 新建 `scripts/start.ps1`（Windows）完成全自动本地启动
- `docker/docker-compose.yml` + `packages/build-engine/frontend/Dockerfile` 完成 build-engine 生产部署
- 所有操作幂等：有了就跳过，变了就重做
- Python 版本变更时自动重建 `.venv`
- `Makefile` 统一入口：`make dev` → `scripts/start.sh`

**Non-Goals:**
- 不切换到 PostgreSQL（保持 SQLite）
- 不修改现有前后端代码逻辑
- 不涉及 CI/CD 配置
- Docker Compose 不处理 SQLite 数据持久化（上 PG 时自然解决）

## Decisions

### Decision 1: Shell script + uv → Python 环境管理
**选择：** 使用 `uv` 代替 `pip` 管理 venv 和依赖安装。
**理由：** `uv venv` / `uv pip install` 比 `pip` 快 10-100 倍，且 venv 创建和依赖安装可一步到位。`uv` 已内建支持 macOS/Linux/Windows。
**替代方案：** 传统的 `pip` + `venv` 标准库 — 更慢但无额外依赖。本项目 CLI 工具链已考虑 `uv`，优先选用。

### Decision 2: Marker 文件机制 → 幂等跳过
**选择：** 用 `.alembic_done`、`.seed_done`、`.requirements.hash` 文本文件标记"已完成"的状态。
**理由：** 简单可靠，无外部依赖。`requirements.txt` 的 md5 hash 确保依赖变更时自动重装。
**替代方案：** 每次都跑然后检查输出 — 更慢；查数据库状态 — 需要 DB 连接。

### Decision 3: `.python-version` → Python 版本跟踪
**选择：** 检测 `.venv/pyvenv.cfg` 中的 version，与 `python3 --version` 比对，不一致则重建。
**理由：** 无需额外文件，pyenv/pipenv 的 `.python-version` 方案也类似。
**替代方案：** 每次检查 — 慢；不检查 — venv 兼容性问题。

### Decision 4: PowerShell → Windows 平台
**选择：** `scripts/start.ps1` 而非 `.bat`。
**理由：** PowerShell 支持结构化逻辑、错误处理、后台进程管理，`cmd.exe` 的 `.bat` 能力有限。Windows 10+ 已内置 PowerShell。

### Decision 5: `scripts/start-backend.sh` → Docker 容器入口
**选择：** backend Dockerfile 的 CMD 指向 `scripts/start-backend.sh`，内部串行执行 migration → seed → exec uvicorn。
**理由：** 比 CMD 中拼 shell 链更可控，方便在 entrypoint 中扩展（如加等待数据库就绪逻辑）。
**替代方案：** CMD 中直接 `alembic ... && python seed.py && uvicorn ...` — 可读性差，难维护。

### Decision 6: nginx → 前端生产部署
**选择：** 前端 Docker 镜像使用 nginx 服务静态构建产物，`/api/` 请求反向代理到 backend。
**理由：** nginx 是成熟的静态文件服务器 + 反向代理，一个 image 搞定。前端不需要在 Node.js 里跑生产。
**替代方案：** 后端统一托管前端静态文件 — 耦合更紧；Node.js 直接 serve — 不如 nginx 高效和安全。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|---------|
| 用户机器未安装 `uv` | 启动脚本中检测并打印安装指引（`curl -LsSf https://astral.sh/uv/install.sh`） |
| Windows 上 `uv` 路径问题 | `scripts/start.ps1` 中通过 `Get-Command uv` 验证，给出 PowerShell 安装命令 |
| 前后端端口被占用 | 打印错误信息提示用户检查端口占用，暂不自动换端口（开发环境依赖 proxy 配置） |
| `scripts/start.sh` 后台进程无法终止 | 脚本注册 SIGINT/SIGTERM trap，用 `kill $PID` 清理两个子进程 |
| Docker 中 SQLite 数据随容器销毁 | 文档注明"生产使用需迁移到 PostgreSQL"，本次不做 volume 挂载 |

## Migration Plan

1. 创建 `packages/build-engine/backend/scripts/start-backend.sh` — Docker 容器入口
2. 创建 `scripts/start.sh` — macOS/Linux 一键启动
3. 创建 `scripts/start.ps1` — Windows 一键启动
4. 创建 `docker/docker-compose.yml` — 生产部署（build context 指向 repo 根，访问 workspace 配置）
5. 创建 `packages/build-engine/backend/Dockerfile` — 后端镜像（python:3.12-slim + uv）
6. 创建 `packages/build-engine/frontend/Dockerfile` — 前端镜像（pnpm 构建 + nginx）
7. 创建 `.dockerignore` — 加速 Docker 构建
8. 更新 `README.md` — 快速开始重写
9. 更新 `.gitignore` — 加入 marker 文件
