import pytest
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_coder_backend():
    return MagicMock()


class TestExecutorServiceRefactored:
    def test_init_with_backend(self, mock_coder_backend):
        from app.services.executor_service import ExecutorService
        svc = ExecutorService(backend=mock_coder_backend)
        assert svc._backend is mock_coder_backend

    def test_init_without_backend_uses_default(self):
        from app.services.executor_service import ExecutorService
        with patch("app.services.executor_service.create_backend") as mock_factory:
            svc = ExecutorService()
            mock_factory.assert_called_once()

    def test_check_prerequisites_docker_available(self):
        from app.services.executor_service import ExecutorService
        with patch("app.services.executor_service.docker") as mock_docker:
            mock_docker.from_env.return_value.ping.return_value = True
            ok, msg = ExecutorService.check_prerequisites()
            assert ok is True
            assert "available" in msg.lower()

    def test_check_prerequisites_docker_unavailable(self):
        from app.services.executor_service import ExecutorService
        with patch("app.services.executor_service.docker") as mock_docker:
            mock_docker.from_env.side_effect = Exception("Docker not found")
            ok, msg = ExecutorService.check_prerequisites()
            assert ok is False
            assert "Docker" in msg
