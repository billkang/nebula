## 1. Docker 基础设施

- [ ] 1.1 创建 `docker/coder/Dockerfile`（基于 nikolaik/python-nodejs:python3.12-nodejs22，预装 ruff/pytest/pytest-cov + @anthropic-ai/claude-code）
- [ ] 1.2 创建 `docker/builder/Dockerfile`（基于 python:3.12-alpine，仅装 git）
- [ ] 1.3 在项目根目录创建或修改 `Makefile`，添加 `build-coder-image` 和 `build-builder-image` 命令
- [ ] 1.4 验证两个 Docker 镜像可正常构建（`make build-coder-image && make build-builder-image`）

## 2. CoderBackend 抽象接口

- [ ] 2.1 创建 `backend/app/services/coder_backend.py`：定义 `CodingResult`、`BuildResult` dataclass
- [ ] 2.2 定义 `CoderBackend` 抽象基类：`execute_coding`、`execute_build`、`cancel` 方法
- [ ] 2.3 创建 `backend/app/services/backends/__init__.py`：注册表 + `register_backend` / `get_backend` / `create_backend` 工厂函数
- [ ] 2.4 `DockerCoderBackend` 在模块导入时自动注册到注册表

## 3. DockerCoderBackend 实现

- [ ] 3.1 创建 `backend/app/services/backends/docker_backend.py`：初始化 DockerClient
- [ ] 3.2 实现 `execute_coding`：启动容器 → 注入 ANTHROPIC_API_KEY → exec_run claude code → 清理
- [ ] 3.3 实现 `execute_build`：启动构建容器 → pip install -r requirements.txt → pytest → 打包 tar.gz+manifest → 清理
- [ ] 3.4 实现 `cancel`：跟踪当前容器 ID，调用 container.stop() 和 container.remove()
- [ ] 3.5 实现 `_build_coding_prompt`：根据 spec 和 skill 构造编码指令文本
- [ ] 3.6 实现 Auth 注入：优先 ANTHROPIC_API_KEY env var，fallback 挂载 ~/.claude/
- [ ] 3.7 实现 Volume 挂载策略：编码容器 rw，构建容器 src/ 为 ro + artifacts/ 为 rw
- [ ] 3.8 实现资源限制：按 settings 中的 CODER_CPU_LIMIT / CODER_MEMORY_LIMIT / BUILDER_CPU_LIMIT / BUILDER_MEMORY_LIMIT 配置
- [ ] 3.9 实现超时机制：构建容器 600s 超时，编码容器 3600s 超时
- [ ] 3.10 实现日志捕获：容器退出后收集 stdout/stderr，失败时写入 CodingResult/BuildResult 的 error 字段

## 4. 配置项

- [ ] 4.1 在 `backend/app/config.py` 新增配置项：`coder_backend` (默认 "docker")、`coder_image` (默认 "nebula-coder:latest")、`builder_image` (默认 "nebula-builder:latest")、`coder_cpu_limit` (默认 2)、`coder_memory_limit` (默认 "2g")、`builder_cpu_limit` (默认 1)、`builder_memory_limit` (默认 "512m")

## 5. ExecutorService 重构

- [ ] 5.1 修改 `ExecutorService` 构造方法，接收可选的 `CoderBackend` 参数（默认从注册表创建）
- [ ] 5.2 `check_prerequisites` 改为检查 Docker daemon 可用性而非 `claude --version`
- [ ] 5.3 `execute` 改为通过 `self._backend.execute_coding()` 执行
- [ ] 5.4 保持现有 API 响应结构不变（status/message 字段）
- [ ] 5.5 状态管理仍使用 dict（本 change 不解决状态持久化）

## 6. BuildService 重构

- [ ] 6.1 修改 `BuildService` 构造方法，接收可选的 `CoderBackend` 参数
- [ ] 6.2 `run_tests` 改为通过 `self._backend.execute_build()` 在构建容器中执行
- [ ] 6.3 `build` 方法中阶段 1（测试）+ 阶段 2（验证）迁入构建容器
- [ ] 6.4 阶段 3（打包）从构建容器的 tar.gz 输出中读取产物
- [ ] 6.5 阶段 4（推送 runtime）保持现有逻辑不变
- [ ] 6.6 `cancel_build` 改为调用 `self._backend.cancel()` + 清理构建容器
- [ ] 6.7 保持现有 API 响应结构不变

## 7. 测试

- [ ] 7.1 单元测试：mock DockerClient，验证 `DockerCoderBackend.execute_coding` 参数传递正确（镜像名、卷挂载、环境变量）
- [ ] 7.2 单元测试：mock DockerClient，验证 `DockerCoderBackend.execute_build` 参数传递正确
- [ ] 7.3 单元测试：验证 `create_backend("docker")` 返回 `DockerCoderBackend` 实例
- [ ] 7.4 单元测试：验证注册表对未知 backend 名称抛出 `ValueError`
- [ ] 7.5 单元测试：验证 `CoderBackend` 抽象类不能被实例化
- [ ] 7.6 单元测试：验证超时和取消逻辑（mock container.stop/remove）
- [ ] 7.7 集成测试（`@pytest.mark.skipif(not docker_available)`）：启动编码容器，验证 Docker daemon 可达
- [ ] 7.8 集成测试：启动构建容器，验证基本构建流程
- [ ] 7.9 运行现有 88 个测试，确认无回归

## 8. 文档

- [ ] 8.1 更新 `docs/roadmap.md` 中的 Phase 2 状态为「进行中」
- [ ] 8.2 更新 `backend/README.md`（如有）说明 Docker 依赖
