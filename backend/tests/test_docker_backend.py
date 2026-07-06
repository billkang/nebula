import os
import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_docker():
    with patch("app.services.backends.docker_backend.docker") as mock:
        mock.from_env.return_value = MagicMock()
        yield mock


class TestDockerCoderBackendInit:
    def test_init_creates_client(self, mock_docker):
        from app.services.backends.docker_backend import DockerCoderBackend
        backend = DockerCoderBackend()
        mock_docker.from_env.assert_called_once()
        assert backend.client is not None


class TestDockerCoderBackendExecuteCoding:
    def test_execute_coding_runs_container(self, mock_docker):
        from app.services.backends.docker_backend import DockerCoderBackend
        mock_client = mock_docker.from_env.return_value
        mock_container = MagicMock()
        mock_container.exec_run.return_value = (0, b"done")
        mock_client.containers.run.return_value = mock_container

        backend = DockerCoderBackend()
        result = backend.execute_coding(
            spec={}, skill=None, project_dir="/tmp/test",
        )

        mock_client.containers.run.assert_called_once()
        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs["image"] == "nebula-coder:latest"
        assert call_kwargs["cpu_count"] == 2
        assert call_kwargs["mem_limit"] == "2g"
        assert result.status == "success"

    def test_execute_coding_env_passes_api_key(self, mock_docker):
        from app.services.backends.docker_backend import DockerCoderBackend
        mock_client = mock_docker.from_env.return_value
        mock_container = MagicMock()
        mock_container.exec_run.return_value = (0, b"done")
        mock_client.containers.run.return_value = mock_container

        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "sk-test-key"}):
            backend = DockerCoderBackend()
            result = backend.execute_coding(
                spec={}, skill=None, project_dir="/tmp/test",
            )

        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs["environment"].get("ANTHROPIC_API_KEY") == "sk-test-key"

    def test_execute_coding_failure(self, mock_docker):
        from app.services.backends.docker_backend import DockerCoderBackend
        mock_client = mock_docker.from_env.return_value
        mock_container = MagicMock()
        mock_container.exec_run.return_value = (1, b"error: module not found")
        mock_client.containers.run.return_value = mock_container

        backend = DockerCoderBackend()
        result = backend.execute_coding(
            spec={}, skill=None, project_dir="/tmp/test",
        )

        assert result.status == "failed"
        assert "module not found" in result.error

    def test_cancel_stops_container(self, mock_docker):
        from app.services.backends.docker_backend import DockerCoderBackend
        mock_client = mock_docker.from_env.return_value
        mock_container = MagicMock()
        mock_client.containers.run.return_value = mock_container

        backend = DockerCoderBackend()
        backend._current_container_id = "abc123"
        backend.client.containers.get.return_value = mock_container

        backend.cancel()
        mock_container.stop.assert_called_once_with(timeout=10)
        mock_container.remove.assert_called_once()


class TestDockerCoderBackendExecuteBuild:
    def test_execute_build_success(self, mock_docker):
        from app.services.backends.docker_backend import DockerCoderBackend
        mock_client = mock_docker.from_env.return_value
        mock_client.containers.run.return_value = b"BUILD_SUCCESS"

        backend = DockerCoderBackend()
        result = backend.execute_build(project_dir="/tmp/test")

        mock_client.containers.run.assert_called_once()
        call_kwargs = mock_client.containers.run.call_args[1]
        assert call_kwargs["image"] == "nebula-builder:latest"
        assert call_kwargs["cpu_count"] == 1
        assert call_kwargs["mem_limit"] == "512m"
        assert result.status == "success"

    def test_execute_build_container_error(self, mock_docker):
        from app.services.backends.docker_backend import DockerCoderBackend
        from docker.errors import ContainerError
        mock_client = mock_docker.from_env.return_value
        mock_client.containers.run.side_effect = ContainerError(
            container=MagicMock(),
            exit_status=1,
            command="pytest",
            image="nebula-builder:latest",
            stderr=b"test failure",
        )

        backend = DockerCoderBackend()
        result = backend.execute_build(project_dir="/tmp/test")

        assert result.status == "failed"
