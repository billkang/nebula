import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path


class TestBuildServiceRefactored:
    def test_init_with_backend(self):
        from app.services.build_service import BuildService
        mock_backend = MagicMock()
        svc = BuildService(backend=mock_backend)
        assert svc._backend is mock_backend

    def test_init_without_backend_uses_default(self):
        from app.services.build_service import BuildService
        with patch("app.services.build_service.create_backend") as mock_factory:
            BuildService()
            mock_factory.assert_called_once()

    def test_verify_integrity_unchanged(self, tmp_path):
        from app.services.build_service import BuildService
        (tmp_path / "src").mkdir()
        (tmp_path / "requirements.txt").write_text("pytest")
        (tmp_path / "Dockerfile").write_text("FROM python")
        missing = BuildService.verify_integrity(tmp_path)
        assert missing == []

    def test_verify_integrity_missing(self, tmp_path):
        from app.services.build_service import BuildService
        (tmp_path / "src").mkdir()
        missing = BuildService.verify_integrity(tmp_path)
        assert "requirements.txt" in missing
        assert "Dockerfile" in missing
