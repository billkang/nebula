## 新增需求

### 需求：Docker Compose 配置
项目根目录 SHALL 提供 `docker/docker-compose.yml` 用于生产部署。

#### 场景：构建并启动所有服务
- **WHEN** 用户运行 `docker compose up --build`
- **THEN** 系统 SHALL：
  - 从 `packages/build-engine/backend/Dockerfile` 构建后端镜像
  - 从 `packages/build-engine/frontend/Dockerfile` 构建前端镜像
  - 在端口 8000 启动后端服务
  - 在端口 80 启动前端服务（通过 nginx）
  - 前端 nginx SHALL 将 `/api/*` 请求代理到后端

#### 场景：后端服务配置
- **WHEN** 后端容器启动
- **THEN** 它 SHALL：
  - 在容器启动时执行 `alembic upgrade head`
  - 在容器启动时执行 `python seed.py`
  - 通过 uvicorn 提供 FastAPI 服务

### 需求：后端 Dockerfile
`packages/build-engine/backend/Dockerfile` SHALL 构建生产可用的 FastAPI 镜像。

#### 场景：后端镜像构建
- **WHEN** Docker 构建后端镜像
- **THEN** 它 SHALL：
  - 使用 `python:3.12-slim` 作为基础镜像，并从 `ghcr.io/astral-sh/uv` 获取 `uv`
  - 通过 `uv sync --frozen` 从 `pyproject.toml` 安装依赖
  - 复制后端源码及同级 workspace 包
  - 暴露端口 8000
  - 设置 CMD 为 `scripts/start-backend.sh` 入口脚本（alembic → seed → uvicorn）

### 需求：前端 Dockerfile
`packages/build-engine/frontend/Dockerfile` SHALL 构建由 nginx 服务的前端生产镜像。

#### 场景：前端镜像构建
- **WHEN** Docker 构建前端镜像
- **THEN** 它 SHALL：
  - 使用 `node:20-alpine` 作为构建阶段，编译 Vite 产物
  - 使用 `nginx:alpine` 作为生产阶段
  - 将构建产物复制到 nginx 服务目录
  - 配置 nginx 将 `/api/` 代理到后端
  - 默认端口 80
