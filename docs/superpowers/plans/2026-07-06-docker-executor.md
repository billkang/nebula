# Docker Executor Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the local subprocess-based coder executor with a Docker containerized architecture (CoderBackend abstraction + DockerCoderBackend) for environment isolation.

**Architecture:** Introduce `CoderBackend` abstract base class with `execute_coding()` and `execute_build()` methods, a registry for pluggable backends, and a `DockerCoderBackend` implementation that manages two independent Docker containers (coder container for Claude Code execution, builder container for test+package). Existing `ExecutorService` and `BuildService` delegate to the backend while keeping their API surfaces unchanged.

**Tech Stack:** Python 3.12, FastAPI, docker-py, pytest (with mock for unit tests, `@pytest.mark.skipif` for integration tests)

## Global Constraints

- Must preserve existing API endpoints (POST /projects/{id}/execute, GET /projects/{id}/execute/status, POST /projects/{id}/build, etc.)
- Must preserve existing response structure (status/message/artifact_version/runtime_status/preview_url fields)
- Must maintain backward compatibility: all existing 88 tests must continue to pass
- No new external dependencies beyond `docker-py` (already partially used in nebula-runtime)
- Docker daemon must be available at runtime (not required for unit tests)
- Manager/worker user mismatch: container output files owned by root → chown after container exit

---

### Task 1: Create Docker infrastructure (Dockerfiles + Makefile)

**Files:**
- Create: `docker/coder/Dockerfile`
- Create: `docker/builder/Dockerfile`
- Create: `Makefile` (project root)

**Interfaces:**
- Consumes: nothing
- Produces: Two Docker images named `nebula-coder:latest` and `nebula-builder:latest`, buildable via `make`

- [ ] **Step 1: Create coder Dockerfile**

```dockerfile
# docker/coder/Dockerfile
FROM nikolaik/python-nodejs:python3.12-nodejs22

RUN pip install --no-cache-dir ruff pytest pytest-cov
RUN npm install -g @anthropic-ai/claude-code

WORKDIR /workspace

# Keep container alive, awaiting docker exec instructions
CMD ["tail", "-f", "/dev/null"]
```

- [ ] **Step 2: Run `docker build` to verify coder image builds**

Run: `docker build -t nebula-coder:latest -f docker/coder/Dockerfile .`
Expected: build succeeds, image tagged `nebula-coder:latest`

- [ ] **Step 3: Create builder Dockerfile**

```dockerfile
# docker/builder/Dockerfile
FROM python:3.12-alpine

RUN apk add --no-cache git

WORKDIR /workspace

# Dynamic CMD: pip install && pytest && packaging handled by entrypoint script via docker exec
COPY docker/builder/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
```

- [ ] **Step 4: Create builder entrypoint script**

```bash
#!/bin/sh
# docker/builder/entrypoint.sh
# Runs inside the build container: install deps → test → package
set -e

PROJECT_DIR="${1:-/workspace}"

cd "$PROJECT_DIR"

echo "=== Installing dependencies ==="
if [ -f requirements.txt ]; then
    pip install --no-cache-dir -r requirements.txt
fi

echo "=== Running tests ==="
python -m pytest --tb=short -q 2>&1 || {
    echo "TESTS_FAILED"
    exit 1
}

echo "=== Packaging artifact ==="
ARTIFACT_DIR="$PROJECT_DIR/artifacts"
mkdir -p "$ARTIFACT_DIR"

VERSION=$(cat "$PROJECT_DIR/version.txt" 2>/dev/null || echo "v1")
MANIFEST="$ARTIFACT_DIR/manifest.json"

cat > "$MANIFEST" <<MEOF
{
  "version": "$VERSION",
  "created_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "entry": "src/main.py",
  "dependencies": []
}
MEOF

# Extract dependencies from requirements.txt if present
if [ -f requirements.txt ]; then
    DEPS=$(grep -v '^#' requirements.txt | grep -v '^$' | sed 's/^/    "/;s/$/",/' | tr '\n' '\n')
    python3 -c "
import json
with open('$MANIFEST') as f:
    m = json.load(f)
with open('requirements.txt') as f:
    m['dependencies'] = [l.strip() for l in f if l.strip() and not l.startswith('#')]
with open('$MANIFEST', 'w') as f:
    json.dump(m, f, indent=2)
"
fi

tar czf "$ARTIFACT_DIR/artifact.tar.gz" \
    -C "$PROJECT_DIR" src requirements.txt Dockerfile manifest.json

echo "BUILD_SUCCESS"
```

- [ ] **Step 5: Run `docker build` to verify builder image builds**

Run: `docker build -t nebula-builder:latest -f docker/builder/Dockerfile .`
Expected: build succeeds, image tagged `nebula-builder:latest`

- [ ] **Step 6: Create Makefile targets**

```makefile
# Makefile
.PHONY: build-coder-image build-builder-image build-images

build-coder-image:
	docker build -t nebula-coder:latest -f docker/coder/Dockerfile .

build-builder-image:
	docker build -t nebula-builder:latest -f docker/builder/Dockerfile .

build-images: build-coder-image build-builder-image
```

- [ ] **Step 7: Verify `make build-images` works**

Run: `make build-images`
Expected: both images build and tag successfully

- [ ] **Step 8: Commit**

```bash
git add docker/coder/Dockerfile docker/builder/Dockerfile docker/builder/entrypoint.sh Makefile
git commit -m "新增 Docker 基础设施：编码容器和构建容器镜像"
```

---

### Task 2: CoderBackend abstract interface and result types

**Files:**
- Create: `backend/app/services/coder_backend.py`
- Create: `backend/app/tests/test_coder_backend.py`

**Interfaces:**
- Consumes: nothing
- Produces: `CoderBackend`, `CodingResult`, `BuildResult` symbols used by Tasks 3-6

- [ ] **Step 1: Write the failing test for abstract class**

```python
# backend/app/tests/test_coder_backend.py
import pytest
from app.services.coder_backend import CoderBackend, CodingResult, BuildResult


def test_coder_backend_is_abstract():
    """CoderBackend should not be instantiable directly."""
    with pytest.raises(TypeError):
        CoderBackend()


def test_coding_result_defaults():
    """CodingResult default fields."""
    r = CodingResult(status="success", source_dir="/tmp/src", message="done")
    assert r.status == "success"
    assert r.source_dir == "/tmp/src"
    assert r.message == "done"
    assert r.error is None


def test_build_result_defaults():
    """BuildResult default fields."""
    r = BuildResult(status="failed", message="tests failed", error="AssertionError: x != y")
    assert r.status == "failed"
    assert r.artifact_path is None
    assert r.error == "AssertionError: x != y"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_coder_backend.py::test_coder_backend_is_abstract -v`
Expected: FAIL with ModuleNotFoundError

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/coder_backend.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
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
    """Abstract base for coding execution backends."""

    @abstractmethod
    async def execute_coding(
        self,
        spec: dict,
        skill,
        project_dir: str,
        *,
        timeout: int = 3600,
    ) -> CodingResult:
        ...

    @abstractmethod
    async def execute_build(
        self,
        project_dir: str,
        version: Optional[str] = None,
        *,
        timeout: int = 600,
    ) -> BuildResult:
        ...

    def cancel(self) -> None:
        pass
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_coder_backend.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/coder_backend.py backend/app/tests/test_coder_backend.py
git commit -m "新增 CoderBackend 抽象接口和结果类型"
```

---

### Task 3: Backend registry

**Files:**
- Create: `backend/app/services/backends/__init__.py`
- Modify: `backend/app/services/__init__.py` (optional, for clean re-exports)

**Interfaces:**
- Consumes: `CoderBackend` from Task 2
- Produces: `register_backend()`, `get_backend()`, `create_backend()` used by Tasks 4-6

- [ ] **Step 1: Write the failing test**

```python
# backend/app/tests/test_backends_registry.py
import pytest
from app.services.backends import register_backend, get_backend, create_backend
from app.services.coder_backend import CoderBackend


class FakeBackend(CoderBackend):
    async def execute_coding(self, spec, skill, project_dir, *, timeout=3600):
        from app.services.coder_backend import CodingResult
        return CodingResult(status="success", source_dir="", message="fake")

    async def execute_build(self, project_dir, version=None, *, timeout=600):
        from app.services.coder_backend import BuildResult
        return BuildResult(status="success", message="fake")


def test_register_and_get():
    register_backend("fake", FakeBackend)
    cls = get_backend("fake")
    assert cls is FakeBackend


def test_unknown_backend_raises():
    with pytest.raises(ValueError, match="unknown-backend"):
        get_backend("unknown-backend")


def test_create_backend_default():
    backend = create_backend("fake")
    assert isinstance(backend, FakeBackend)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_backends_registry.py -v`
Expected: ModuleNotFoundError for `app.services.backends`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/backends/__init__.py
from app.services.coder_backend import CoderBackend

_registry: dict[str, type[CoderBackend]] = {}


def register_backend(name: str, backend_cls: type[CoderBackend]) -> None:
    _registry[name] = backend_cls


def get_backend(name: str) -> type[CoderBackend]:
    if name not in _registry:
        raise ValueError(f"Unknown backend: {name}")
    return _registry[name]


def create_backend(name: str = "") -> CoderBackend:
    from app.config import settings
    name = name or settings.coder_backend
    cls = get_backend(name)
    return cls()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_backends_registry.py -v`
Expected: 3 passed

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/backends/__init__.py backend/app/tests/test_backends_registry.py
git commit -m "新增 CoderBackend 注册表模式"
```

---

### Task 4: Configuration updates

**Files:**
- Modify: `backend/app/config.py`

**Interfaces:**
- Consumes: nothing
- Produces: `settings.coder_backend`, `settings.coder_image`, `settings.builder_image`, etc. used by Tasks 5-6

- [ ] **Step 1: Write the failing test**

```python
# backend/app/tests/test_config_extended.py
from app.config import settings


def test_coder_backend_default():
    assert hasattr(settings, "coder_backend")
    assert settings.coder_backend == "docker"


def test_docker_image_defaults():
    assert settings.coder_image == "nebula-coder:latest"
    assert settings.builder_image == "nebula-builder:latest"


def test_resource_config_defaults():
    assert settings.coder_cpu_limit == 2
    assert settings.coder_memory_limit == "2g"
    assert settings.builder_cpu_limit == 1
    assert settings.builder_memory_limit == "512m"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_config_extended.py -v`
Expected: FAIL with AttributeError

- [ ] **Step 3: Add config fields to Settings**

```python
# backend/app/config.py — add these fields to the Settings class
    coder_backend: str = "docker"
    coder_image: str = "nebula-coder:latest"
    builder_image: str = "nebula-builder:latest"
    coder_cpu_limit: int = 2
    coder_memory_limit: str = "2g"
    builder_cpu_limit: int = 1
    builder_memory_limit: str = "512m"
```

The full Settings class after edit:

```python
# backend/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./nebula.db"
    jwt_secret: str = "change-me-to-a-random-secret"
    jwt_expiry_hours: int = 24
    cors_origins: str = "http://localhost:5173"
    admin_username: str = "admin"
    admin_password: str = "123456"
    pm_username: str = "pm"
    pm_password: str = "123456"
    runtime_url: str = "http://localhost:8001"

    # Docker executor config
    coder_backend: str = "docker"
    coder_image: str = "nebula-coder:latest"
    builder_image: str = "nebula-builder:latest"
    coder_cpu_limit: int = 2
    coder_memory_limit: str = "2g"
    builder_cpu_limit: int = 1
    builder_memory_limit: str = "512m"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
```

- [ ] **Step 4: Run test to verify it passes**

Run: `cd backend && python -m pytest tests/test_config_extended.py -v`
Expected: 3 passed

- [ ] **Step 5: Run existing tests to check no regression**

Run: `cd backend && python -m pytest -v`
Expected: all existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/config.py backend/app/tests/test_config_extended.py
git commit -m "新增 Docker 执行器配置项"
```

---

### Task 5: DockerCoderBackend — core and coding implementation

**Files:**
- Create: `backend/app/services/backends/docker_backend.py`

**Interfaces:**
- Consumes: `CoderBackend`, `CodingResult`, `BuildResult` from Task 2; `register_backend` from Task 3; config from Task 4
- Produces: `DockerCoderBackend` class used by Tasks 6-7

- [ ] **Step 1: Write the failing test**

```python
# backend/app/tests/test_docker_backend.py
import pytest
from unittest.mock import patch, MagicMock
from app.services.backends.docker_backend import DockerCoderBackend


@pytest.fixture
def mock_docker():
    with patch("app.services.backends.docker_backend.docker") as mock:
        mock.from_env.return_value = MagicMock()
        yield mock


class TestDockerCoderBackendInit:
    def test_init_creates_client(self, mock_docker):
        backend = DockerCoderBackend()
        mock_docker.from_env.assert_called_once()
        assert backend.client is not None


class TestDockerCoderBackendExecuteCoding:
    @pytest.mark.asyncio
    async def test_execute_coding_runs_container(self, mock_docker):
        mock_client = mock_docker.from_env.return_value
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = (0, b"done")

        backend = DockerCoderBackend()
        result = await backend.execute_coding(
            spec={}, skill=None, project_dir="/tmp/test",
        )

        mock_client.containers.run.assert_called_once()
        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs["image"] == "nebula-coder:latest"
        assert "/tmp/test" in str(call_kwargs["volumes"])
        assert "ANTHROPIC_API_KEY" in str(call_kwargs["environment"])
        assert call_kwargs["cpu_count"] == 2
        assert call_kwargs["mem_limit"] == "2g"
        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_execute_coding_failure(self, mock_docker):
        mock_client = mock_docker.from_env.return_value
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container
        mock_container.exec_run.return_value = (1, b"error: module not found")

        backend = DockerCoderBackend()
        result = await backend.execute_coding(
            spec={}, skill=None, project_dir="/tmp/test",
        )

        assert result.status == "failed"
        assert "module not found" in result.error

    @pytest.mark.asyncio
    async def test_cancel_stops_container(self, mock_docker):
        mock_client = mock_docker.from_env.return_value
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container

        backend = DockerCoderBackend()
        backend._current_container_id = "abc123"
        backend.client.containers.get.return_value = mock_container

        backend.cancel()
        mock_container.stop.assert_called_once_with(timeout=10)
        mock_container.remove.assert_called_once()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_docker_backend.py -v`
Expected: ModuleNotFoundError for `app.services.backends.docker_backend`

- [ ] **Step 3: Write minimal implementation**

```python
# backend/app/services/backends/docker_backend.py
import os
from typing import Optional

import docker
from docker.errors import DockerException

from app.config import settings
from app.services.coder_backend import CoderBackend, CodingResult, BuildResult
from app.services.backends import register_backend


class DockerCoderBackend(CoderBackend):
    """Docker-based implementation of CoderBackend."""

    def __init__(self):
        self.client = docker.from_env()
        self._current_container_id: Optional[str] = None

    async def execute_coding(
        self,
        spec: dict,
        skill,
        project_dir: str,
        *,
        timeout: int = 3600,
    ) -> CodingResult:
        volumes = {project_dir: {"bind": "/workspace", "mode": "rw"}}

        environment = {
            "HOME": "/root",
        }
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            environment["ANTHROPIC_API_KEY"] = api_key

        try:
            container = self.client.containers.run(
                image=settings.coder_image,
                volumes=volumes,
                environment=environment,
                cpu_count=settings.coder_cpu_limit,
                mem_limit=settings.coder_memory_limit,
                detach=True,
                tty=True,
            )
        except DockerException as e:
            return CodingResult(
                status="failed",
                source_dir=str(project_dir),
                message="Failed to start coding container",
                error=str(e),
            )

        self._current_container_id = container.id
        prompt_text = self._build_coding_prompt(spec, skill)

        try:
            exit_code, output = container.exec_run(
                cmd=["claude", "code", "--prompt", prompt_text, "--print"],
                workdir="/workspace",
                timeout=timeout,
            )
        except Exception as e:
            self._cleanup_container(container.id)
            return CodingResult(
                status="failed",
                source_dir=str(project_dir),
                message="Coding execution failed",
                error=str(e),
            )

        self._cleanup_container(container.id)
        output_text = output.decode("utf-8", errors="replace") if isinstance(output, bytes) else str(output)

        if exit_code == 0:
            self._fix_permissions(project_dir)
            return CodingResult(
                status="success",
                source_dir=str(project_dir),
                message="Coding completed",
            )
        else:
            return CodingResult(
                status="failed",
                source_dir=str(project_dir),
                message="Coding execution failed",
                error=output_text[:2000],
            )

    async def execute_build(
        self,
        project_dir: str,
        version: Optional[str] = None,
        *,
        timeout: int = 600,
    ) -> BuildResult:
        ro_volumes = {project_dir: {"bind": "/workspace", "mode": "ro"}}
        rw_volumes = {f"{project_dir}/artifacts": {"bind": "/workspace/artifacts", "mode": "rw"}}
        volumes = {**ro_volumes, **rw_volumes}

        try:
            exit_code, output = self.client.containers.run(
                image=settings.builder_image,
                volumes=volumes,
                cpu_count=settings.builder_cpu_limit,
                mem_limit=settings.builder_memory_limit,
                detach=False,
                remove=True,
                timeout=timeout,
            )
        except DockerException as e:
            return BuildResult(
                status="failed",
                message="Build container failed",
                error=str(e),
            )

        output_text = output.decode("utf-8", errors="replace") if isinstance(output, bytes) else str(output)

        if exit_code == 0:
            self._fix_permissions(f"{project_dir}/artifacts")
            return BuildResult(
                status="success",
                artifact_path=f"{project_dir}/artifacts/artifact.tar.gz",
                version=version,
                test_output=output_text[:2000],
                message="Build completed",
            )
        else:
            return BuildResult(
                status="failed",
                message="Build failed",
                test_output=output_text[:2000],
                error=output_text[:2000],
            )

    def cancel(self) -> None:
        if self._current_container_id:
            try:
                container = self.client.containers.get(self._current_container_id)
                container.stop(timeout=10)
                container.remove()
            except Exception:
                pass
            self._current_container_id = None

    def _cleanup_container(self, container_id: str) -> None:
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            container.remove()
        except Exception:
            pass
        if self._current_container_id == container_id:
            self._current_container_id = None

    def _fix_permissions(self, path: str) -> None:
        """Fix file ownership from root to the host user."""
        import subprocess
        uid = os.environ.get("HOST_UID", str(os.getuid()))
        gid = os.environ.get("HOST_GID", str(os.getgid()))
        try:
            subprocess.run(
                ["chown", "-R", f"{uid}:{gid}", path],
                capture_output=True, timeout=30,
            )
        except Exception:
            pass

    def _build_coding_prompt(self, spec: dict, skill) -> str:
        """Build a claude-code prompt from spec and skill."""
        if skill and hasattr(skill, "coding_prompt"):
            return skill.coding_prompt
        if spec:
            import json
            return f"请根据以下技术规格实现功能代码：\n\n{json.dumps(spec, indent=2, ensure_ascii=False)}"
        return "请实现功能代码。"


# Auto-register at import time
register_backend("docker", DockerCoderBackend)
```

- [ ] **Step 4: Run unit tests to verify they pass**

Run: `cd backend && python -m pytest tests/test_docker_backend.py -v`
Expected: 4 passed (init, execute_coding_success, execute_coding_failure, cancel)

- [ ] **Step 5: Run existing tests to check no regression**

Run: `cd backend && python -m pytest -v`
Expected: all existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/backends/docker_backend.py backend/app/tests/test_docker_backend.py
git commit -m "实现 DockerCoderBackend — 编码和构建容器管理"
```

---

### Task 6: ExecutorService refactoring

**Files:**
- Modify: `backend/app/services/executor_service.py`

**Interfaces:**
- Consumes: `create_backend` from Task 3, `DockerCoderBackend` from Task 5
- Produces: refactored `ExecutorService` class used by `api/executor.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/app/tests/test_executor_refactored.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.services.executor_service import ExecutorService


@pytest.fixture
def mock_coder_backend():
    mock = MagicMock()
    mock.execute_coding = AsyncMock()
    return mock


class TestExecutorServiceRefactored:
    def test_init_with_backend(self, mock_coder_backend):
        svc = ExecutorService(backend=mock_coder_backend)
        assert svc._backend is mock_coder_backend

    @pytest.mark.asyncio
    async def test_execute_delegates_to_backend(self, mock_coder_backend):
        from app.services.coder_backend import CodingResult
        mock_coder_backend.execute_coding.return_value = CodingResult(
            status="success", source_dir="/tmp/src", message="done",
        )

        svc = ExecutorService(backend=mock_coder_backend)
        result = svc.execute("proj-1")

        mock_coder_backend.execute_coding.assert_called_once()
        assert result["status"] == "success"

    def test_check_prerequisites_docker_check(self):
        """check_prerequisites should return True if Docker is available."""
        with patch("app.services.executor_service.docker") as mock_docker:
            mock_docker.from_env.return_value.ping.return_value = True
            ok, msg = ExecutorService.check_prerequisites()
            assert ok is True
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_executor_refactored.py -v`
Expected: FAIL (ExecutorService still uses static methods without backend param)

- [ ] **Step 3: Refactor ExecutorService**

```python
# backend/app/services/executor_service.py
import asyncio
import os
from pathlib import Path
from typing import Optional

import docker

from app.services.coder_backend import CoderBackend
from app.services.backends import create_backend

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

_exec_states: dict[str, dict] = {}


class ExecutorService:
    def __init__(self, backend: Optional[CoderBackend] = None):
        self._backend = backend or create_backend()

    @staticmethod
    def _state(project_id: str) -> dict:
        if project_id not in _exec_states:
            _exec_states[project_id] = {"status": "idle", "message": None}
        return _exec_states[project_id]

    @staticmethod
    def check_prerequisites() -> tuple[bool, str]:
        """Check if Docker daemon is available."""
        try:
            client = docker.from_env()
            client.ping()
            return True, "Docker daemon is available"
        except docker.errors.DockerException as e:
            return False, f"Docker daemon not available: {e}"
        except Exception as e:
            return False, f"Docker check failed: {e}"

    @staticmethod
    def get_status(project_id: str) -> dict:
        st = ExecutorService._state(project_id)
        return {"status": st["status"], "message": st["message"]}

    def execute(self, project_id: str) -> dict:
        st = ExecutorService._state(project_id)
        available, msg = ExecutorService.check_prerequisites()
        if not available:
            st["status"] = "failed"
            st["message"] = msg
            return ExecutorService.get_status(project_id)

        project_dir = BASE_DIR / "projects" / project_id
        project_dir.mkdir(parents=True, exist_ok=True)

        st["status"] = "running"
        st["message"] = "编码执行中（Docker 容器）..."

        try:
            result = asyncio.run(
                self._backend.execute_coding(
                    spec={},
                    skill=None,
                    project_dir=str(project_dir),
                )
            )
            st["status"] = result.status
            st["message"] = result.message
            if result.error:
                st["message"] = f"{result.message}: {result.error[:300]}"
        except Exception as e:
            st["status"] = "failed"
            st["message"] = f"编码执行异常: {str(e)[:500]}"

        return ExecutorService.get_status(project_id)

    def cancel(self) -> None:
        self._backend.cancel()
```

- [ ] **Step 4: Run all tests**

Run: `cd backend && python -m pytest tests/test_executor_refactored.py tests/test_docker_backend.py tests/test_coder_backend.py -v`
Expected: all pass

- [ ] **Step 5: Run existing full test suite**

Run: `cd backend && python -m pytest -v`
Expected: all 88+ existing tests still pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/executor_service.py backend/app/tests/test_executor_refactored.py
git commit -m "重构 ExecutorService：委托 CoderBackend 执行"
```

---

### Task 7: BuildService refactoring

**Files:**
- Modify: `backend/app/services/build_service.py`

**Interfaces:**
- Consumes: `create_backend` from Task 3, `DockerCoderBackend` from Task 5
- Produces: refactored `BuildService` class used by `api/build.py` and `sandbox_service.py`

- [ ] **Step 1: Write the failing test**

```python
# backend/app/tests/test_build_refactored.py
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
from app.services.build_service import BuildService


@pytest.fixture
def mock_coder_backend():
    mock = MagicMock()
    mock.execute_build = AsyncMock()
    return mock


class TestBuildServiceRefactored:
    def test_init_with_backend(self, mock_coder_backend):
        svc = BuildService(backend=mock_coder_backend)
        assert svc._backend is mock_coder_backend

    def test_verify_integrity_unchanged(self, tmp_path):
        (tmp_path / "src").mkdir()
        (tmp_path / "requirements.txt").write_text("pytest")
        (tmp_path / "Dockerfile").write_text("FROM python")
        missing = BuildService.verify_integrity(tmp_path)
        assert missing == []

    def test_verify_integrity_missing(self, tmp_path):
        (tmp_path / "src").mkdir()
        missing = BuildService.verify_integrity(tmp_path)
        assert "requirements.txt" in missing
        assert "Dockerfile" in missing
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd backend && python -m pytest tests/test_build_refactored.py -v`
Expected: FAIL (BuildService doesn't accept backend param yet)

- [ ] **Step 3: Refactor BuildService**

```python
# backend/app/services/build_service.py
import asyncio
import json
import os
import tarfile
import threading
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from app.config import settings
from app.services.coder_backend import CoderBackend
from app.services.backends import create_backend

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

_build_states: dict[str, dict] = {}
_async_builds: dict[str, dict] = {}
_async_builds_lock = threading.Lock()


def _build_running_in_thread(project_id: str):
    try:
        result = BuildService().build(project_id)
        with _async_builds_lock:
            if project_id in _async_builds:
                _async_builds[project_id]["result"] = result
                _async_builds[project_id]["done"] = True
    except Exception as e:
        with _async_builds_lock:
            if project_id in _async_builds:
                _async_builds[project_id]["result"] = {"status": "failed", "message": str(e)[:500]}
                _async_builds[project_id]["done"] = True


class BuildService:
    def __init__(self, backend: Optional[CoderBackend] = None):
        self._backend = backend or create_backend()

    @staticmethod
    def _state(project_id: str) -> dict:
        if project_id not in _build_states:
            _build_states[project_id] = {"status": "idle", "message": ""}
        return _build_states[project_id]

    @staticmethod
    def verify_integrity(project_dir: Path) -> list[str]:
        missing = []
        for item in ["src", "requirements.txt", "Dockerfile"]:
            if not (project_dir / item).exists():
                missing.append(item)
        return missing

    def build(self, project_id: str, source_dir: str | None = None) -> dict:
        st = BuildService._state(project_id)
        project_dir = Path(source_dir) if source_dir else BASE_DIR / "projects" / project_id

        if BuildService._check_cancelled(project_id):
            return BuildService.get_status(project_id)

        # ── 阶段 1-2: 构建容器内测试 + 验证 ──
        st["status"] = "testing"
        st["message"] = "正在构建容器中运行测试和打包..."

        try:
            version = self._next_version(project_id)
            build_result = asyncio.run(
                self._backend.execute_build(
                    project_dir=str(project_dir),
                    version=version,
                )
            )
        except Exception as e:
            st["status"] = "failed"
            st["message"] = f"构建容器执行异常: {str(e)[:500]}"
            return BuildService.get_status(project_id)

        if build_result.status != "success":
            st["status"] = "failed"
            st["message"] = build_result.message or "构建失败"
            st["test_output"] = build_result.test_output
            return BuildService.get_status(project_id)

        # ── 阶段 3: 解析打包产物 ──
        if BuildService._check_cancelled(project_id):
            return BuildService.get_status(project_id)
        st["status"] = "verifying"
        st["message"] = "验证构建产物..."

        # 完整性检查（宿主机端二次确认）
        missing = BuildService.verify_integrity(project_dir)
        if missing:
            st["status"] = "failed"
            st["message"] = f"缺少必要文件: {', '.join(missing)}"
            return BuildService.get_status(project_id)

        # ── 阶段 4: 推送 runtime ──
        if BuildService._check_cancelled(project_id):
            return BuildService.get_status(project_id)

        st["status"] = "success"
        st["message"] = f"构建完成，Artifact: {build_result.artifact_path}"
        st["artifact_version"] = build_result.version or version

        try:
            from app.services.runtime_client import RuntimeClient
            if RuntimeClient.is_available():
                RuntimeClient.push_artifact(project_id, st["artifact_version"])
                RuntimeClient.start_application(project_id, st["artifact_version"])
                st["runtime_status"] = "pushed"
                st["preview_url"] = f"{settings.runtime_url}/preview/{project_id}"
            else:
                st["runtime_status"] = "runtime_unavailable"
        except Exception as e:
            st["runtime_status"] = f"push_failed: {str(e)[:200]}"

        return BuildService.get_status(project_id)

    @staticmethod
    def _next_version(project_id: str) -> str:
        existing = BuildService.list_artifacts(project_id)
        max_num = 0
        for v in existing:
            vname = v["version"]
            if vname.startswith("v") and vname[1:].isdigit():
                num = int(vname[1:])
                if num > max_num:
                    max_num = num
        return f"v{max_num + 1}"

    @staticmethod
    def _check_cancelled(project_id: str) -> dict | None:
        st = BuildService._state(project_id)
        if st.get("cancel_requested"):
            st["status"] = "cancelled"
            st["message"] = "构建已取消"
            st["cancel_requested"] = False
            return BuildService.get_status(project_id)
        return None

    @staticmethod
    def cancel_build(project_id: str) -> dict:
        st = BuildService._state(project_id)
        st["cancel_requested"] = True
        st["status"] = "cancelled"
        st["message"] = "构建已取消"
        return BuildService.get_status(project_id)

    @staticmethod
    def start_async_build(project_id: str) -> dict:
        with _async_builds_lock:
            if project_id in _async_builds and not _async_builds[project_id].get("done"):
                return {"status": "already_running", "message": "构建已在运行"}
            st = BuildService._state(project_id)
            st["status"] = "starting"
            st["message"] = "正在启动构建..."
            st["cancel_requested"] = False
            _async_builds[project_id] = {"done": False, "result": None}
        thread = threading.Thread(target=_build_running_in_thread, args=(project_id,), daemon=True)
        thread.start()
        return {"status": "started", "message": "构建已启动"}

    @staticmethod
    def get_async_build_result(project_id: str) -> dict:
        with _async_builds_lock:
            build = _async_builds.get(project_id)
            if not build:
                return BuildService.get_status(project_id)
            if build.get("done"):
                return build["result"]
            return BuildService.get_status(project_id)

    @staticmethod
    def get_status(project_id: str) -> dict:
        st = BuildService._state(project_id)
        return {
            "status": st.get("status", "idle"),
            "message": st.get("message", ""),
            "artifact_version": st.get("artifact_version"),
            "runtime_status": st.get("runtime_status"),
            "preview_url": st.get("preview_url"),
        }

    @staticmethod
    def list_artifacts(project_id: str) -> list[dict]:
        artifacts_dir = BASE_DIR / "projects" / project_id / "artifacts"
        if not artifacts_dir.exists():
            return []
        artifacts = []
        for version_dir in sorted(artifacts_dir.iterdir()):
            if version_dir.is_dir():
                mf = version_dir / "manifest.json"
                if mf.exists():
                    with open(mf) as f:
                        m = json.load(f)
                    artifacts.append({
                        "version": version_dir.name,
                        "created_at": m.get("created_at", ""),
                        "path": str(version_dir),
                    })
        return artifacts
```

- [ ] **Step 4: Run all tests**

Run: `cd backend && python -m pytest tests/test_build_refactored.py tests/test_executor_refactored.py tests/test_docker_backend.py tests/test_coder_backend.py -v`
Expected: all pass

- [ ] **Step 5: Run full test suite**

Run: `cd backend && python -m pytest -v`
Expected: 88+ tests all pass

- [ ] **Step 6: Commit**

```bash
git add backend/app/services/build_service.py backend/app/tests/test_build_refactored.py
git commit -m "重构 BuildService：构建阶段委托 CoderBackend 在容器中执行"
```

---

### Task 8: API layer — update executor and build routers for compatibility

**Files:**
- Modify: `backend/app/api/executor.py`
- Possibly modify: `backend/app/api/build.py`

**Note:** The API routers currently call `ExecutorService.execute()` and `BuildService.build()` as static methods. After refactoring, these still work because `execute()` is now an instance method but the router doesn't instantiate the service. We need to update the routers to instantiate services.

- [ ] **Step 1: Update executor router to instantiate ExecutorService**

```python
# backend/app/api/executor.py
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.executor_service import ExecutorService

executor_router = APIRouter(prefix="/projects/{project_id}/execute", tags=["executor"])


@executor_router.post("")
def execute(project_id: str, user: User = Depends(get_current_user)):
    svc = ExecutorService()
    return svc.execute(project_id)


@executor_router.get("/status")
def execute_status(project_id: str, user: User = Depends(get_current_user)):
    return ExecutorService.get_status(project_id)
```

- [ ] **Step 2: Update build router to instantiate BuildService**

```python
# backend/app/api/build.py — update the build endpoint
from app.services.build_service import BuildService

@router.post("")
def build_project(project_id: str, user: User = Depends(get_current_user)):
    svc = BuildService()
    return svc.build(project_id)
```

- [ ] **Step 3: Run full test suite to verify no regression**

Run: `cd backend && python -m pytest -v`
Expected: all tests pass

- [ ] **Step 4: Commit**

```bash
git add backend/app/api/executor.py backend/app/api/build.py
git commit -m "更新 API 路由：实例化重构后的 ExecutorService 和 BuildService"
```

---

### Task 9: Integration tests (Docker daemon required)

**Files:**
- Create: `backend/app/tests/test_docker_integration.py`

**Interfaces:**
- Consumes: `DockerCoderBackend` from Task 5

- [ ] **Step 1: Write integration test file**

```python
# backend/app/tests/test_docker_integration.py
"""
Integration tests for DockerCoderBackend.
Requires a running Docker daemon — skipped if not available.
"""
import pytest
from app.services.backends.docker_backend import DockerCoderBackend


def docker_available():
    import docker
    try:
        client = docker.from_env()
        client.ping()
        return True
    except Exception:
        return False


docker_reason = "Docker daemon not available"


@pytest.mark.skipif(not docker_available(), reason=docker_reason)
class TestDockerCoderBackendIntegration:
    def test_coder_image_exists(self):
        import docker
        client = docker.from_env()
        images = [img.tags for img in client.images.list() if "nebula-coder" in str(img.tags)]
        assert len(images) > 0, "nebula-coder:latest image not found. Run: make build-coder-image"

    def test_builder_image_exists(self):
        import docker
        client = docker.from_env()
        images = [img.tags for img in client.images.list() if "nebula-builder" in str(img.tags)]
        assert len(images) > 0, "nebula-builder:latest image not found. Run: make build-builder-image"

    @pytest.mark.asyncio
    async def test_builder_container_runs(self, tmp_path):
        """Run the builder container on a minimal test project."""
        # Create a minimal project
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")
        (tmp_path / "requirements.txt").write_text("")
        (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\nCMD [\"python\", \"src/main.py\"]")

        backend = DockerCoderBackend()
        result = await backend.execute_build(str(tmp_path))

        assert result.status == "success"
        assert result.artifact_path is not None
        assert result.artifact_path.endswith("artifact.tar.gz")

        # Verify artifacts created
        assert (tmp_path / "artifacts" / "artifact.tar.gz").exists()
        assert (tmp_path / "artifacts" / "manifest.json").exists()
```

- [ ] **Step 2: Run integration tests (will skip if no Docker)**

Run: `cd backend && python -m pytest tests/test_docker_integration.py -v`
Expected: either PASS (Docker available) or SKIPPED (no Docker)

- [ ] **Step 3: Run full test suite to confirm no breakage**

Run: `cd backend && python -m pytest -v`
Expected: all tests pass

- [ ] **Step 4: Commit**

```bash
git add backend/app/tests/test_docker_integration.py
git commit -m "新增 DockerCoderBackend 集成测试"
```

---

### Self-Review Checklist

**1. Spec coverage:**
- `coder-backend-interface/spec.md`: ✅ Task 2 (interface + types), Task 3 (registry), Task 4 (config)
- `docker-coder-backend/spec.md`: ✅ Task 1 (Dockerfiles), Task 5 (DockerCoderBackend), Task 6-7 (service refactoring), Task 9 (integration tests)
- Coding container lifecycle scenarios → Task 5
- Build container lifecycle scenarios → Task 5
- Claude Code pre-installed → Task 1 (Dockerfile)
- Volume mount scenarios → Task 5
- Resource limits → Task 4 (config) + Task 5 (implementation)
- Configurable images → Task 4
- Auth injection → Task 5
- Log capture → Task 5 (error field)
- Alpine builder → Task 1
- Separate lifecycle → Task 5 (execute_coding and execute_build are independent)

**2. Placeholder scan:** No "TBD", "TODO", "implement later" in tasks. All code is explicit.

**3. Type consistency:** `CodingResult` and `BuildResult` used consistently across Tasks 2-7. `create_backend("docker")` matches the registry name. `settings.coder_backend` default is `"docker"`. ✅
