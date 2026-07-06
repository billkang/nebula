## 1. nebula-runtime 项目脚手架

- [x] 1.1 创建 `nebula-runtime/` 目录结构和 `app/` 包初始化
- [x] 1.2 创建 `requirements.txt`（fastapi, uvicorn, docker-py, pydantic-settings）
- [x] 1.3 创建 `app/main.py` FastAPI 应用入口（含 CORS、错误处理、lifespan）
- [x] 1.4 创建 `app/config.py` pydantic-settings 配置（RUNTIME_PORT, ARTIFACTS_DIR, PLATFORM_URL）
- [x] 1.5 创建 `Dockerfile` + `docker-compose.yml` 一行命令启动
- [x] 1.6 创建 `.env.example` 环境变量模板
- [x] 1.7 创建 `tests/` 目录和 `conftest.py` 测试配置

## 2. Artifact Registry 服务

- [ ] 2.1 实现 `app/services/registry_service.py`：Artifact 文件存储与读取逻辑
- [ ] 2.2 实现 Artifact 版本自增逻辑（基于现有文件目录自动计算下一个版本号）
- [ ] 2.3 实现 `manifest.json` 内容验证（必填字段检查）
- [ ] 2.4 实现 Artifact 磁盘结构校验（缺少 src/requirements.txt/Dockerfile 时报错）
- [ ] 2.5 实现 `app/api/registry.py`：`POST /api/v1/registry/artifacts/:project` 注册新 Artifact
- [ ] 2.6 实现 `GET /api/v1/registry/artifacts` 列出项目 Artifact 版本列表
- [ ] 2.7 实现 `GET /api/v1/registry/artifacts/:project/:version` 获取版本详情
- [ ] 2.8 实现 `DELETE /api/v1/registry/artifacts/:project/:version` 删除指定版本
- [ ] 2.9 编写 registry_service 相关 pytest 测试

## 3. Docker 容器管理服务

- [ ] 3.1 实现 `app/services/container_service.py`：Docker SDK 封装（build/run/stop/logs）
- [ ] 3.2 实现 `docker_build(image_tag, dockerfile_dir)` — 从 Artifact 构建镜像
- [ ] 3.3 实现 `docker_run(image_tag, cpus, memory, port)` — 启动容器并设置资源限制
- [ ] 3.4 实现 `docker_stop(container_id)` — 停止并移除容器
- [ ] 3.5 实现 `docker_status()` — 查询当前运行中的容器
- [ ] 3.6 实现 `docker_logs(container_id, tail=100)` — 获取最近日志
- [ ] 3.7 实现 `health_check()` — 等待应用健康检查通过（最多 30s 超时）
- [ ] 3.8 实现自动清理：启动新应用时自动 stop 当前运行中的容器
- [ ] 3.9 实现前置检查：启动时检测 Docker daemon 可用性
- [ ] 3.10 编写 container_service 相关 pytest 测试

## 4. Runtime API

- [ ] 4.1 实现 `POST /api/v1/runtime/start` — 加载 Artifact + 构建镜像 + 启动容器
- [ ] 4.2 实现 `POST /api/v1/runtime/stop` — 停止当前应用
- [ ] 4.3 实现 `GET /api/v1/runtime/status` — 查询运行状态（running/idle）
- [ ] 4.4 实现 `GET /api/v1/runtime/logs` — 获取运行日志
- [ ] 4.5 实现 `GET /health` — 健康检查端点
- [ ] 4.6 实现 `POST /api/v1/runtime/push` — 接收 platform 推送的 Artifact
- [ ] 4.7 实现 `GET /api/v1/runtime/versions` — 列出可用 Artifact 版本
- [ ] 4.8 实现 `POST /api/v1/runtime/start` 中的错误处理（Artifact 不存在、build 失败等）
- [ ] 4.9 编写 runtime API 相关 pytest 测试

## 5. nebula-platform 集成（推送 Artifact 到 Runtime）

- [ ] 5.1 在 platform 的 build_service.py 构建完成后增加 push 到 runtime 的步骤
- [ ] 5.2 实现 push 逻辑：打包 Artifact（tar.gz）+ manifest → HTTP POST 到 runtime
- [ ] 5.3 在 platform 前端 Chat 页面的构建成功状态后增加"预览"按钮
- [ ] 5.4 预览按钮跳转到 nebula-runtime 提供的业务应用 URL
- [ ] 5.5 在 platform 前端显示 runtime 运行状态（加载中/运行中/已停止/失败）
- [ ] 5.6 配置 platform 端 runtime_url 环境变量

## 6. 端到端集成测试

- [ ] 6.1 编写集成测试：构建完成 → push → runtime 加载 → 应用可访问
- [ ] 6.2 编写集成测试：重复 push 新版本 → 自动停止旧版 → 启动新版
- [ ] 6.3 编写集成测试：push 损坏 Artifact → runtime 返回合理错误
- [ ] 6.4 编写集成测试：runtime 不可用时 platform 优雅降级
- [ ] 6.5 编写 README.md（启动方式、配置说明、与 platform 对接步骤）
