## Why

星云平台的编码执行和构建验证当前通过宿主机的 subprocess 直接调用 `claude code` 和 `pytest`，存在三个实际问题：`pip install` 等操作会污染宿主机 Python 环境；构建结果依赖宿主机已安装的包版本，不可复现；无法限制编码任务的 CPU/内存资源。此外，ExecutorService 和 BuildService 与 subprocess 紧耦合，未来 A2A 网关（Phase 4）缺少可扩展的抽象接入点。

## What Changes

- 创建 **CoderBackend** 抽象基类，定义编码执行后端的标准接口
- 实现 **DockerCoderBackend**：双容器模式（编码容器 + 构建容器），负责编码和构建的全流程容器化
- 构建 **编码容器（coder image）**：大镜像，含 Python、Node.js、Claude Code SDK、开发工具链。Claude Code 授权通过挂载宿主机凭证解决
- 构建 **构建容器（builder image）**：小镜像（alpine + Python），负责 pip install → pytest → 打包 tar.gz
- **重构 ExecutorService**：从 subprocess 硬编码改为接入 DockerCoderBackend
- **重构 BuildService**：构建阶段迁入构建容器，保持构建隔离性
- 通过 Docker volume 挂载实现宿主机、编码容器、构建容器之间的源码和产物传递
- CoderBackend 接口为 Phase 4 的 A2A 实现预留扩展点

## Capabilities

### New Capabilities

- `coder-backend-interface`: 编码执行后端的抽象接口与可插拔架构
- `docker-coder-backend`: Docker 容器化编码执行与构建验证后端

### Modified Capabilities

无（不修改现有功能接口，仅重构内部实现）

## Out of Scope

本 change 第一版明确不做：

- **多容器并行编排**：同一项目编码和构建串行执行，不并行编排多个编码任务。永久 v1 out
- **Kubernetes 部署容器化执行**：容器管理仅限于本机 Docker daemon，不引入 K8s 编排。永久 v1 out
- **A2A CoderBackend 实现**：CoderBackend 接口预留扩展点，但 A2A 实现推迟到 Phase 4（协议网关）。v2
- **编码容器 UI 终端流式日志**：容器日志仅在后端捕获，不在前端提供终端视图。v2
- **镜像 CI/CD 自动构建与推送**：Dockerfile 提供但没有 CI pipeline 自动构建和推送到 registry。未来
- **SubprocessCoderBackend（回退实现）**：当前没有替换期间的后备方案。改 change 不保留旧的 subprocess 路径。v2
- **高并发/分布式环境**：不考虑多个平台实例共享同一 Docker daemon 的场景。永久 v1 out

## Impact

- **修改代码库**：`backend/app/services/executor_service.py` 重构，`backend/app/services/build_service.py` 重构
- **新增代码**：`backend/app/services/coder_backend.py`（抽象接口），`backend/app/services/backends/docker_backend.py`（Docker 实现）
- **新增依赖**：Docker SDK for Python（已有部分使用，需确保完整可用）
- **新增构建产物**：Dockerfile 文件（编码镜像 Dockerfile + 构建镜像 Dockerfile）
- **新增配置项**：编码镜像名称/标签、构建镜像名称/标签、容器资源限制参数
- **外部依赖**：宿主机须安装 Docker daemon，编码容器内依赖 Claude Code CLI
- **不影响现有用户接口**：API 端点不变，前端无改动
- **不影响 nebula-runtime**：现有预览容器机制不修改

## Known Limitations

- **容器启动延迟**：每次编码任务需启动 Docker 容器，相比当前 subprocess 直调用会增加 2-5s 延迟。编码任务本身耗时较长（分钟级），容器启动延迟可忽略，但构建任务的启动延迟相对明显
- **镜像版本黏性**：`@anthropic-ai/claude-code` 在构建镜像时锁定版本，后续更新需主动 rebuild 镜像。建议用 CI 每周自动 rebuild 或使用 `latest` 标签
- **产物文件所有权**：容器内生成的源码和产物文件归属 `root`，宿主机开发者可能需要 `sudo` 才能操作。需在容器内使用非 root 用户或退出容器时执行 `chown`
- **Docker daemon 依赖**：本 design 强依赖宿主机 Docker daemon 可用。`check_prerequisites` 须返回明确的错误信息，避免"装了平台但运行不了"的体验断层
