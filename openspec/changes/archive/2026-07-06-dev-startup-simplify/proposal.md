## Why

Nebula 当前启动流程需要分别在 `packages/build-engine/backend/` 和 `packages/build-engine/frontend/` 目录下手动执行 6+ 步命令（建 venv、装依赖、配环境、迁移数据库、初始化数据、启动服务），新开发者上手门槛高，日常开发重复劳动多。同时缺乏生产环境的容器化部署方案。

## What Changes

- 增强 `scripts/start.sh` — 增加 Python 版本检测自动重建 venv，增加 uv/npm 前置检查
- 新增 `scripts/start.ps1` — Windows 一键启动脚本
- 新增 `docker/docker-compose.yml` — build-engine 生产 Docker 部署
- 更新 `Makefile` — 完善 `dev`、`build-engine` 等入口
- 更新 `README.md` — 快速开始改为一键启动为首选方式
- 更新 `.gitignore` — 加入 marker 文件（`*.done`, `*.hash`）

## Capabilities

### New Capabilities

- `local-dev-startup`: 本地开发环境一键启动，覆盖 macOS/Linux/Windows，自动处理依赖安装、数据库迁移、种子数据
- `production-deployment`: 基于 Docker Compose 的生产环境部署配置

### Modified Capabilities

（无 — 本次不修改现有代码行为）

## Impact

| 维度 | 影响 |
|------|------|
| 工具链 | 引入 `uv` 作为 Python 包管理（之前为 pip），新增 npm/uv 为前置依赖 |
| 文档 | README 快速开始部分重写，新增启动脚本使用说明 |
| 项目文件 | 根目录新增 `scripts/start.ps1`，更新 `scripts/start.sh`，新增 `docker/docker-compose.yml`，更新 `Makefile` |
| 配置 | 无新增配置（前端使用硬编码相对路径 `/api/v1/...`，无需 `.env`） |
| 安全性 | 无影响（不修改认证/授权逻辑） |
| 开发体验 | 正向：新开发者一条命令启动；负向：Windows 用户需额外安装 Git Bash 或使用 PowerShell 脚本 |

## Known Limitations

1. **Marker 文件散落于 backend 目录** — `.alembic_done`、`.seed_done`、`.requirements.hash` 集中在 `packages/build-engine/backend/` 下。后续若增加更多服务，需为每个服务维护单独 marker，缺乏统一管理机制。
2. **`scripts/start.ps1` 存在同步偏移风险** — 后续 `scripts/start.sh` 新增功能可能不同步到 PowerShell 版本，导致双平台能力差异逐步扩大。无自动化同步机制。
3. **启动顺序轮询等待** — 前端通过 Python socket 轮询后端端口（最多 30 秒），等待后端就绪后启动。若网络环境特殊或端口检测方式变更，需同步更新检测逻辑。
