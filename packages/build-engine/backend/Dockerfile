# ── Nebula Build Engine 后端镜像 ──
FROM python:3.12-slim
WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 先复制依赖文件（利用 Docker 缓存层）
COPY pyproject.toml uv.lock ./
COPY packages/shared-python/ packages/shared-python/
COPY packages/build-engine/backend/ packages/build-engine/backend/

# 安装生产依赖（不含 dev 依赖）
RUN uv sync --frozen --no-dev --directory packages/build-engine/backend

# 容器默认工作目录在 backend 下
WORKDIR /app/packages/build-engine/backend

# 入口脚本包含 migration + seed + uvicorn 启动链
RUN chmod +x /app/packages/build-engine/backend/scripts/start-backend.sh

EXPOSE 8000
CMD ["/app/packages/build-engine/backend/scripts/start-backend.sh"]
