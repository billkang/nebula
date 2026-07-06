## 1. 增强现有启动脚本

- [x] 1.1 增强 `scripts/start.sh` — 添加 Python 版本检测 + uv/npm 前置检查（已有脚本，增量修改）

## 2. 新建本地启动脚本

- [x] 2.1 新建 `scripts/start.ps1` — Windows 一键启动脚本

## 3. Docker 部署

- [x] 3.1 新建 `packages/build-engine/frontend/Dockerfile` — pnpm 构建 + nginx 镜像
- [x] 3.2 新建 `packages/build-engine/backend/Dockerfile` — python:3.12-slim + uv
- [x] 3.3 新建 `packages/build-engine/backend/scripts/start-backend.sh` — 容器入口（migration → seed → uvicorn）
- [x] 3.4 新建 `docker/docker-compose.yml` — build-engine 生产部署编排（root build context + healthcheck）

## 4. 构建入口

- [x] 4.1 更新 `Makefile` — 添加 build-engine docker-compose 入口

## 5. 文档与配置

- [x] 5.1 更新 `README.md` — 快速开始改为一键启动 + monorepo 适配
- [x] 5.2 更新 `.gitignore` — 加入 marker 文件
