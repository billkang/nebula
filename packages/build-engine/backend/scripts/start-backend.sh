#!/bin/sh
#
# start-backend.sh — Nebula build-engine 后端容器入口
#
# 确保数据库迁移和数据初始化在 uvicorn 启动前完成，
# 避免容器启动后服务尚未就绪。
#
set -e

cd /app/packages/build-engine/backend

# 数据库迁移
uv run alembic upgrade head

# 初始化内置用户
uv run python seed.py

# 启动 uvicorn（exec 替换 shell 进程，确保信号正确传递）
exec uv run uvicorn app.main:app --host 0.0.0.0 --port 8000
