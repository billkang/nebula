## Context

星云平台 MVP v1 的编码执行和构建验证通过宿主机 subprocess 实现。ExecutorService 直接调用 `claude code --prompt`，BuildService 直接运行 `python -m pytest`。两者均使用模块级 dict 管理状态（重启丢失），且与 subprocess 紧耦合。

Phase 2（docker-executor）将此架构提升为可插拔的 CoderBackend 抽象 + Docker 容器化实现，解决环境隔离和可复现性问题，并为 Phase 4（A2A Gateway）预留扩展点。

## Goals / Non-Goals

**Goals:**
- 定义 `CoderBackend` 抽象接口，支持多种编码后端实现
- 实现 `DockerCoderBackend`：编码容器（跑 Claude Code）+ 构建容器（测试 + 打包）
- 重构 `ExecutorService` → 通过 CoderBackend 执行编码
- 重构 `BuildService` → 通过 CoderBackend 执行构建（构建容器内测试 + 打包）
- 保留现有 API 端点，前端无感知改动

**Non-Goals:**
- 多容器并行编排（同一项目串行）
- Kubernetes 部署
- A2A CoderBackend（Phase 4）
- 容器异地/分布式执行
- 编码容器 UI 终端流式日志
- 镜像 CI/CD 自动构建推送

## Change Scope Matrix

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/services/coder_backend.py` | **新增** | CoderBackend 抽象基类 + 结果类型 |
| `backend/app/services/backends/__init__.py` | **新增** | 后端模块包 |
| `backend/app/services/backends/docker_backend.py` | **新增** | DockerCoderBackend 实现 |
| `backend/app/services/executor_service.py` | **修改** | 从 subprocess → 委托 CoderBackend |
| `backend/app/services/build_service.py` | **修改** | 构建阶段委托 CoderBackend（关键路径走容器） |
| `backend/app/config.py` | **修改** | 新增 Docker/Backend 配置项 |
| `docker/coder/Dockerfile` | **新增** | 编码容器 Dockerfile |
| `docker/builder/Dockerfile` | **新增** | 构建容器 Dockerfile |
| `Makefile` | **新增/修改** | 构建镜像命令 |
| 现有 API 路由 (`executor.py`, `build.py`) | **不做修改** | 接口不变 |

## Decisions

### 1. CoderBackend 接口设计

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class CodingResult:
    status: str  # "success" | "failed" | "cancelled" | "timeout"
    source_dir: str
    message: str
    error: Optional[str] = None


@dataclass
class BuildResult:
    status: str  # "success" | "failed" | "cancelled" | "timeout"
    artifact_path: Optional[str] = None
    version: Optional[str] = None
    test_output: Optional[str] = None
    error: Optional[str] = None


class CoderBackend(ABC):
    """编码执行后端抽象。"""

    @abstractmethod
    async def execute_coding(
        self, spec: dict, skill, project_dir: str, *, timeout: int = 3600
    ) -> CodingResult:
        """启动编码容器/进程，执行编码 → 产出源码。"""
        ...

    @abstractmethod
    async def execute_build(
        self, project_dir: str, version: Optional[str] = None, *, timeout: int = 600
    ) -> BuildResult:
        """启动构建容器/进程，测试 + 打包。"""
        ...

    def cancel(self) -> None:
        """取消当前正在执行的操作。"""
        pass
```

**为何拆为两个方法而非一个：** 编码容器（长时间交互）和构建容器（一次性短任务）的生命周期不同。后续 A2A 实现也可能分别代理编码和构建到不同服务。

**为何用 dataclass 而非 Pydantic：** 接口层无需序列化，dataclass 轻量且与 Pydantic 可互转。

### 2. CoderBackend 注册与选择

```python
# backend/app/services/backends/__init__.py

_registry: dict[str, type[CoderBackend]] = {}

def register_backend(name: str, backend_cls: type[CoderBackend]) -> None:
    _registry[name] = backend_cls

def get_backend(name: str) -> type[CoderBackend]:
    if name not in _registry:
        raise ValueError(f"Unknown backend: {name}")
    return _registry[name]

def create_backend(name: str = "") -> CoderBackend:
    name = name or settings.coder_backend or "docker"
    cls = get_backend(name)
    return cls()
```

**启动时自动注册：** `DockerCoderBackend` 在模块导入时调用 `register_backend("docker", DockerCoderBackend)`。

**为何用简单注册表而非 DI 框架：** 项目当前不使用 DI 框架（FastAPI 也没有 DI），注册表模式零依赖、可测试。

### 3. 编码容器镜像

```dockerfile
# docker/coder/Dockerfile
FROM nikolaik/python-nodejs:python3.12-nodejs22

# Python 开发工具
RUN pip install --no-cache-dir ruff pytest pytest-cov

# 安装 Claude Code CLI
RUN npm install -g @anthropic-ai/claude-code

# 工作目录
WORKDIR /workspace

# 默认命令：等待指令
CMD ["tail", "-f", "/dev/null"]
```

**Base 镜像选择理由：** `nikolaik/python-nodejs` 是社区流行的 Python+Node.js 组合镜像，在 Docker Hub 有超过 100M 下载量。若需要更可控的基础镜像可在后续迭代中替换为组合 Dockerfile。

**Claude Code 预装：** 容器自包含，开发者不需要本地安装 Claude Code。授权通过环境变量 `ANTHROPIC_API_KEY` 注入。

**CMD tail -f /dev/null：** 容器启动后保持运行，等待 `docker exec` 或 `claude code --prompt` 指令。

### 4. 构建容器镜像

```dockerfile
# docker/builder/Dockerfile
FROM python:3.12-alpine

# 安装构建依赖（git 用于 pip install git+ 仓库）
RUN apk add --no-cache git

WORKDIR /workspace

# 构建任务通过 docker run --rm 一次性执行
# CMD 由 DockerCoderBackend 动态指定
CMD ["python", "-m", "pytest"]
```

### 5. Volume 挂载策略

两个容器共用宿主机项目目录：

```
宿主机: /projects/<project-id>/
  dirs: src/, artifacts/

编码容器: docker run -v /projects/<project-id>/:/workspace
  → 读写 /workspace/src/ (Claude Code 产出)

构建容器: docker run -v /projects/<project-id>/:/workspace:ro
          -v /projects/<project-id>/artifacts/:/workspace/artifacts/
  → 只读 /workspace/src/, 写入 /workspace/artifacts/
```

**为何不用 docker cp：** volume 挂载是实时同步的，构建过程出错时宿主机可直接查看产出。`docker cp` 仅限于容器退出后拷贝，调试不友好。

**文件所有权处理：** 容器内进程默认以 root 运行，产出文件属 root。编码容器退出后，DockerCoderBackend 在宿主机侧执行 `chown -R $(id -u):$(id -g)` 恢复所有权为当前用户。构建容器产物同理。

### 6. DockerCoderBackend 实现策略

```python
class DockerCoderBackend(CoderBackend):
    def __init__(self):
        self.client = docker.from_env()
        self._current_container_id: Optional[str] = None

    async def execute_coding(self, spec, skill, project_dir, *, timeout=3600):
        container = self.client.containers.run(
            image=settings.coder_image,
            volumes={project_dir: {"bind": "/workspace", "mode": "rw"}},
            environment={
                "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
                "HOME": "/root",
            },
            cpu_count=settings.coder_cpu_limit,
            mem_limit=settings.coder_memory_limit,
            detach=True,
            tty=True,
        )
        self._current_container_id = container.id
        # 构造编码指令并执行
        instruction = self._build_coding_prompt(spec, skill)
        exit_code, output = container.exec_run(
            ["claude", "code", "--prompt", instruction, "--print"],
            workdir="/workspace",
            timeout=timeout,
        )
        self._cleanup_container(container.id)
        if exit_code == 0:
            return CodingResult(status="success", source_dir=str(project_dir / "src"), message="编码执行完成")
        else:
            return CodingResult(status="failed", source_dir=str(project_dir / "src"),
                                message="编码执行失败", error=output.decode()[:2000])

    def _build_coding_prompt(self, spec, skill) -> str:
        """根据 spec 和 skill 构造 claude code 指令文本。"""
        ...

    def _cleanup_container(self, container_id):
        try:
            c = self.client.containers.get(container_id)
            c.stop(timeout=10)
            c.remove()
        except docker.errors.NotFound:
            pass
```

### 7. 授权注入策略

| 有 `ANTHROPIC_API_KEY` | 行为 |
|------------------------|------|
| 有 | 作为环境变量传入编码容器 |
| 无 | 尝试挂载 `~/.claude/` 目录到容器内 `/root/.claude/` |

**为何优先使用环境变量：** Claude Code CLI 检测到 `ANTHROPIC_API_KEY` 环境变量时优先使用，不需要交互式登录。挂载目录方案需要宿主机和容器内用户路径一致，可靠性较低。

### 8. ExecutorService 重构

现有 ExecutorService 内所有 `@staticmethod` 改为实例方法，保留对外 API 签名不变：

```python
class ExecutorService:
    def __init__(self, backend: Optional[CoderBackend] = None):
        self._backend = backend or create_backend()
        ...

    def execute(self, project_id: str) -> dict:
        # 改为：
        result = asyncio.run(self._backend.execute_coding(spec, skill, project_dir))
        ...
```

**状态管理仍然使用 dict（本 change 不解决状态持久化问题）。**

### 9. BuildService 重构

BuildService 的测试和打包阶段迁入构建容器：

```python
class BuildService:
    def __init__(self, backend: Optional[CoderBackend] = None):
        self._backend = backend or create_backend()

    def build(self, project_id: str, source_dir: str | None = None) -> dict:
        # 阶段 1-2（测试 + 验证）→ 通过 backend.execute_build() 在构建容器中完成
        result = asyncio.run(self._backend.execute_build(project_dir))
        if result.status != "success":
            ...
        # 阶段 3（打包产物解析）→ 宿主机读取 tar.gz
        # 阶段 4（推送 runtime）→ 不变
```

**注意：** `verify_integrity`（检查 src/, requirements.txt, Dockerfile）改为在卷挂载后由构建容器内脚本执行。

## Risks / Trade-offs

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| Docker daemon 不可用 | 编码和构建完全不可用 | check_prerequisites 改为检测 Docker daemon，返回明确错误 |
| 镜像体积大 | 首次构建慢 | Docker layer caching，Dockerfile 分层优化 |
| 编码容器内 Claude Code 授权失败 | 编码容器空跑 | 注入前验证 ANTHROPIC_API_KEY 有效性或 ~/.claude/ 是否存在 |
| 容器内文件权限问题 | 产出文件归属 root，宿主机无法修改 | 容器内使用非 root 用户，或者构建后 chown |
| 并行构建冲突 | 同一项目多个构建请求冲突 | 维持串行策略，请求冲突时返回 "already_running" |
| Docker socket 暴露 | 安全风险 | 限制容器只能访问必要的 socket；编码容器和构建容器不用挂载 docker.sock |
| 容器日志累积 | 磁盘占用 | 成功完成后自动清理容器；失败容器保留日志但设置保留上限 |

## Migration Plan

**不涉及数据迁移。** 改动集中在 service 层，API 接口不变。部署步骤：

1. 创建 Dockerfile（编码镜像 + 构建镜像）
2. 实现 CoderBackend 抽象接口和结果类型
3. 实现 DockerCoderBackend
4. `make build-coder-image && make build-builder-image` 构建镜像
5. 重构 ExecutorService → 接入 CoderBackend
6. 重构 BuildService → 接入 CoderBackend
7. 添加配置项到 config.py
8. 跑测试：单元测试（mock Docker）+ 集成测试（real Docker）
9. 验证：API 端点返回与之前相同的响应结构

**回退：** 配置项 `CODER_BACKEND=subprocess`（保留一个 SubprocessCoderBackend 实现作为 fallback，指向旧的 subprocess 逻辑 — *注意：不在本 change 范围内，但架构上预留*）。
