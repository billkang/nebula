"""单元测试 — ContainerService（mock Docker SDK，不依赖真实 Docker daemon）"""
from pathlib import Path
from unittest.mock import patch, MagicMock, call

import pytest
import requests
from docker.errors import DockerException

from app.services.container_service import ContainerService, ContainerError


@pytest.fixture(autouse=True)
def reset_service():
    """每个测试前重置 ContainerService 类状态（类变量共享）。"""
    ContainerService._client = None
    ContainerService._current_container_id = None
    ContainerService._current_project_id = None
    ContainerService._current_version = None
    ContainerService._app_port = None
    yield


@pytest.fixture
def mock_docker_client():
    """创建 mock Docker client。"""
    client = MagicMock()
    client.ping.return_value = True
    client.version.return_value = {"Version": "24.0.0"}
    return client


@pytest.fixture
def sample_artifact_dir(tmp_path):
    """创建带有 Dockerfile 的模拟 Artifact 目录。"""
    artifact_dir = tmp_path / "artifact"
    artifact_dir.mkdir()

    src_dir = artifact_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('hello')")

    (artifact_dir / "requirements.txt").write_text("fastapi\n")
    (artifact_dir / "Dockerfile").write_text("FROM python:3.12-slim\nCMD python src/main.py\n")

    return artifact_dir


class TestContainerService:

    def test_get_client_creates_and_pings(self, mock_docker_client):
        """_get_client() 应创建 docker client 并 ping。"""
        with patch("docker.from_env", return_value=mock_docker_client):
            client = ContainerService._get_client()
            assert client is mock_docker_client
            mock_docker_client.ping.assert_called_once()

    def test_get_client_daemon_unavailable(self):
        """Docker daemon 不可用时应抛出 ContainerError。"""
        with patch("docker.from_env", side_effect=DockerException("connection refused")):
            with pytest.raises(ContainerError, match="Docker daemon not available"):
                ContainerService._get_client()

    def test_check_prerequisites_ok(self, mock_docker_client):
        """Docker daemon 正常时 check_prerequisites 返回成功。"""
        with patch("docker.from_env", return_value=mock_docker_client):
            ok, msg = ContainerService.check_prerequisites()
            assert ok is True
            assert "Docker" in msg
            assert "24.0.0" in msg

    def test_check_prerequisites_fail(self):
        """Docker daemon 不可用时 check_prerequisites 返回失败。"""
        with patch("docker.from_env", side_effect=DockerException("not available")):
            ok, msg = ContainerService.check_prerequisites()
            assert ok is False

    def test_start_stops_existing_container_first(self, mock_docker_client, sample_artifact_dir):
        """start() 应先停止已有容器再启动新容器。"""
        mock_container = MagicMock()
        mock_container.id = "container-new"
        mock_docker_client.containers.run.return_value = mock_container

        # Mock 镜像构建
        mock_image = MagicMock()
        mock_docker_client.images.build.return_value = (mock_image, [])

        with (
            patch("docker.from_env", return_value=mock_docker_client),
            patch("app.services.container_service.ContainerService._wait_for_health", return_value=True),
            patch("socket.socket") as mock_socket,
        ):
            # 模拟已有一个运行中的容器
            ContainerService._current_container_id = "container-old"

            # Mock socket 返回端口
            mock_sock_instance = MagicMock()
            mock_sock_instance.getsockname.return_value = ("", 54321)
            mock_socket.return_value.__enter__.return_value = mock_sock_instance

            # 启动新容器
            result = ContainerService.start(sample_artifact_dir, "proj-test", "v2")

            # 验证旧容器被停止
            mock_docker_client.containers.get.assert_any_call("container-old")
            mock_docker_client.containers.get.return_value.stop.assert_called_once_with(timeout=10)

            # 验证新容器启动
            mock_docker_client.images.build.assert_called_once()
            mock_docker_client.containers.run.assert_called_once()

            assert result["status"] == "running"
            assert result["container_id"] == "container-new"

    def test_start_build_failure(self, mock_docker_client, sample_artifact_dir):
        """Docker build 失败时返回明确错误信息。"""
        from docker.errors import DockerException
        mock_docker_client.images.build.side_effect = DockerException("Build failed: syntax error")

        with (
            patch("docker.from_env", return_value=mock_docker_client),
            patch("socket.socket") as mock_socket,
        ):
            mock_sock_instance = MagicMock()
            mock_sock_instance.getsockname.return_value = ("", 54321)
            mock_socket.return_value.__enter__.return_value = mock_sock_instance

            with pytest.raises(ContainerError, match="Docker build failed"):
                ContainerService.start(sample_artifact_dir, "proj-test", "v1")

    def test_start_run_failure(self, mock_docker_client, sample_artifact_dir):
        """Docker run 失败时抛出 ContainerError。"""
        from docker.errors import APIError
        mock_image = MagicMock()
        mock_docker_client.images.build.return_value = (mock_image, [])
        mock_docker_client.containers.run.side_effect = APIError("port conflict")

        with (
            patch("docker.from_env", return_value=mock_docker_client),
            patch("socket.socket") as mock_socket,
        ):
            mock_sock_instance = MagicMock()
            mock_sock_instance.getsockname.return_value = ("", 54321)
            mock_socket.return_value.__enter__.return_value = mock_sock_instance

            with pytest.raises(ContainerError, match="Failed to start container"):
                ContainerService.start(sample_artifact_dir, "proj-test", "v1")

    def test_start_applies_resource_limits(self, mock_docker_client, sample_artifact_dir):
        """启动容器时应应用 --cpus=1 和 --memory=512m。"""
        mock_container = MagicMock()
        mock_container.id = "container-limits"
        mock_docker_client.containers.run.return_value = mock_container
        mock_image = MagicMock()
        mock_docker_client.images.build.return_value = (mock_image, [])

        with (
            patch("docker.from_env", return_value=mock_docker_client),
            patch("app.services.container_service.ContainerService._wait_for_health", return_value=True),
            patch("socket.socket") as mock_socket,
        ):
            mock_sock_instance = MagicMock()
            mock_sock_instance.getsockname.return_value = ("", 54321)
            mock_socket.return_value.__enter__.return_value = mock_sock_instance

            ContainerService.start(sample_artifact_dir, "proj-test", "v1")

            # 验证容器资源限制被传递
            run_kwargs = mock_docker_client.containers.run.call_args.kwargs
            assert run_kwargs["mem_limit"] == "512m"
            assert run_kwargs["nano_cpus"] == int(1.0 * 1e9)

    def test_stop_when_running(self, mock_docker_client):
        """有运行的容器时，stop 应停止并清理状态。"""
        ContainerService._current_container_id = "container-abc"
        ContainerService._current_project_id = "proj-test"
        ContainerService._current_version = "v1"
        ContainerService._app_port = 54321

        with patch("docker.from_env", return_value=mock_docker_client):
            result = ContainerService.stop()

            mock_docker_client.containers.get.assert_called_once_with("container-abc")
            mock_docker_client.containers.get.return_value.stop.assert_called_once_with(timeout=10)
            assert result["status"] == "stopped"
            assert ContainerService._current_container_id is None
            assert ContainerService._current_project_id is None
            assert ContainerService._current_version is None
            assert ContainerService._app_port is None

    def test_stop_when_idle(self):
        """没有运行的容器时，stop 返回 idle。"""
        result = ContainerService.stop()
        assert result["status"] == "idle"

    def test_status_running(self, mock_docker_client):
        """容器运行时 status 应返回 running 状态。"""
        ContainerService._current_container_id = "container-abc"
        ContainerService._current_project_id = "proj-test"
        ContainerService._current_version = "v1"
        ContainerService._app_port = 54321

        mock_container = MagicMock()
        mock_container.attrs = {
            "State": {
                "Status": "running",
                "StartedAt": "2026-07-06T08:00:00Z",
            }
        }
        mock_docker_client.containers.get.return_value = mock_container

        with patch("docker.from_env", return_value=mock_docker_client):
            status = ContainerService.status()
            assert status["status"] == "running"
            assert status["project_id"] == "proj-test"
            assert status["version"] == "v1"

    def test_status_idle(self):
        """没有运行容器时 status 返回 idle。"""
        status = ContainerService.status()
        assert status["status"] == "idle"

    def test_status_container_disappeared(self, mock_docker_client):
        """容器意外消失时，状态应自动恢复为 idle。"""
        from docker.errors import NotFound
        ContainerService._current_container_id = "container-ghost"

        mock_docker_client.containers.get.side_effect = NotFound("no such container")

        with patch("docker.from_env", return_value=mock_docker_client):
            status = ContainerService.status()
            assert status["status"] == "idle"
            assert ContainerService._current_container_id is None

    def test_logs_when_running(self, mock_docker_client):
        """运行中的容器应返回最近日志。"""
        ContainerService._current_container_id = "container-abc"

        mock_container = MagicMock()
        mock_container.logs.return_value = b"2026-07-06 INFO: app started\n"
        mock_docker_client.containers.get.return_value = mock_container

        with patch("docker.from_env", return_value=mock_docker_client):
            logs = ContainerService.logs(tail=100)
            assert "INFO: app started" in logs
            mock_container.logs.assert_called_once_with(tail=100, timestamps=True)

    def test_logs_when_idle(self):
        """没有运行容器时 logs 返回空字符串。"""
        assert ContainerService.logs() == ""

    def test_health_check_success(self):
        """健康检查在 200 时返回 True。"""
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            result = ContainerService._wait_for_health("http://localhost:54321/health")
            assert result is True

    def test_health_check_timeout(self):
        """健康检查超时后返回 False。"""
        with (
            patch("requests.get", side_effect=requests.ConnectionError("connection refused")),
            patch("app.services.container_service.HEALTH_CHECK_TIMEOUT_S", 1),
            patch("app.services.container_service.HEALTH_CHECK_INTERVAL_S", 0.1),
        ):
            result = ContainerService._wait_for_health("http://localhost:54321/health")
            assert result is False
