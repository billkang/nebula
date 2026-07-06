---
date: 2026-07-06
change: dev-startup-simplify
---

# Brainstorming Session — 一键启动改造

## 讨论主题

Nebula 项目启动流程优化：从多步手动操作改造为一键式启动。

## 关键决策

- 使用新 change `dev-startup-simplify` 单独处理启动脚本，不合并到已有的 `infrastructure` change
- 脚本选用 `uv` 管理 Python 环境（而非 pip/poetry）
- 所有幂等操作（迁移、种子数据）通过 marker 文件标记"已执行"，跳过重复执行
- 采用 `start.sh`（bash） + `start.bat`/`start.ps1`（Windows）双平台策略

## 需求要点

| # | 功能点 | 说明 |
|---|--------|------|
| 1 | `start.sh` | macOS/Linux 一键启动，自动完成 venv → dep → .env → migrate → seed → 启动 |
| 2 | `start.bat` / `start.ps1` | Windows 兼容版本 |
| 3 | `docker-compose.yml` | 生产环境 Docker 部署配置 |
| 4 | 前端 `.env` 处理 | 脚本自动生成 `frontend/.env`（VITE_API_URL 等） |
| 5 | Python 版本变化检测 | `.venv` 自动重建（如果 Python 版本变了） |
| 6 | README 更新 | 快速开始改为一键启动优先，分步启动为备选 |
| 7 | `.gitignore` 更新 | 加入 marker 文件（`.alembic_done` / `.seed_done` / `.requirements.hash`） |

## 边界范围

| # | 不做 | 原因 |
|---|------|------|
| 1 | 不切换到 PostgreSQL | 保持 SQLite，数据库迁移推迟到后续独立变更 |
| 2 | 不改动现有代码逻辑 | 纯工具和文档变更 |
| 3 | 不涉及 CI/CD | 超出本次范围，后续单独讨论 |

## 注意事项

| # | 约束 / 风险 | 处理方式 |
|---|-------------|---------|
| 1 | 需要 `uv` 和 `npm` 在 PATH 中 | 脚本中检查前置条件，缺失时报错并提示安装 |
| 2 | `start.bat` / `start.ps1` 需单独维护部分逻辑 | Windows 无 `uv run` 直接对应，需用 `.venv\\Scripts\\python` |
| 3 | Docker Compose 环境变量需整理 | `docker-compose.yml` 引用 `.env` 或单独 `docker.env` |
| 4 | Python 版本检测 | 读取 `.venv/pyvenv.cfg` 中的 `version`，与 `python3 --version` 比对 |
