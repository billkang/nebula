import json
import tempfile
from pathlib import Path

import pytest

from app.services.registry_service import RegistryService, RegistryError


@pytest.fixture
def registry():
    service = RegistryService()
    return service


@pytest.fixture
def sample_artifact_dir(tmp_path):
    """Create a sample artifact directory with src/, requirements.txt, Dockerfile."""
    artifact_dir = tmp_path / "sample-artifact"
    artifact_dir.mkdir()

    src_dir = artifact_dir / "src"
    src_dir.mkdir()
    (src_dir / "main.py").write_text("print('hello')")

    (artifact_dir / "requirements.txt").write_text("fastapi\nuvicorn\n")
    (artifact_dir / "Dockerfile").write_text("FROM python:3.12-slim\nCMD python src/main.py\n")

    return artifact_dir


class TestRegistryService:

    def test_verify_integrity_ok(self, sample_artifact_dir):
        missing = RegistryService.verify_integrity(sample_artifact_dir)
        assert missing == []

    def test_verify_integrity_missing_src(self, tmp_path):
        bad = tmp_path / "bad"
        bad.mkdir()
        (bad / "requirements.txt").write_text("")
        (bad / "Dockerfile").write_text("")
        missing = RegistryService.verify_integrity(bad)
        assert "src" in missing

    def test_validate_manifest_ok(self):
        manifest = {"version": "v1", "created_at": "now", "entry": "main.py"}
        missing = RegistryService.validate_manifest(manifest)
        assert missing == []

    def test_validate_manifest_missing_fields(self):
        manifest = {"version": "v1"}
        missing = RegistryService.validate_manifest(manifest)
        assert "created_at" in missing
        assert "entry" in missing

    def test_next_version_empty(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr("app.services.registry_service.settings.artifacts_dir", tmpdir)
            version = RegistryService._next_version("proj-a")
            assert version == "v1"

    def test_next_version_increment(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr("app.services.registry_service.settings.artifacts_dir", tmpdir)
            proj_dir = Path(tmpdir) / "proj-a"
            proj_dir.mkdir(parents=True)

            (proj_dir / "v1").mkdir()
            assert RegistryService._next_version("proj-a") == "v2"

            (proj_dir / "v2").mkdir()
            (proj_dir / "v5").mkdir()
            assert RegistryService._next_version("proj-a") == "v6"

    def test_register_artifact(self, monkeypatch, sample_artifact_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr("app.services.registry_service.settings.artifacts_dir", tmpdir)
            result = RegistryService.register_artifact("proj-a", str(sample_artifact_dir))
            assert result["version"] == "v1"
            assert result["status"] == "ready"
            assert "manifest" in result

    def test_register_artifact_missing_src(self, monkeypatch, tmp_path):
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr("app.services.registry_service.settings.artifacts_dir", tmpdir)
            bad = tmp_path / "bad"
            bad.mkdir()
            with pytest.raises(RegistryError, match="Missing required"):
                RegistryService.register_artifact("proj-a", str(bad))

    def test_list_versions(self, monkeypatch, sample_artifact_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr("app.services.registry_service.settings.artifacts_dir", tmpdir)
            RegistryService.register_artifact("proj-a", str(sample_artifact_dir))
            versions = RegistryService.list_versions("proj-a")
            assert len(versions) == 1
            assert versions[0]["version"] == "v1"

    def test_get_version(self, monkeypatch, sample_artifact_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr("app.services.registry_service.settings.artifacts_dir", tmpdir)
            RegistryService.register_artifact("proj-a", str(sample_artifact_dir))
            info = RegistryService.get_version("proj-a", "v1")
            assert info["version"] == "v1"
            assert info["status"] == "ready"

    def test_get_version_not_found(self):
        with pytest.raises(RegistryError, match="not found"):
            RegistryService.get_version("proj-a", "v999")

    def test_delete_version(self, monkeypatch, sample_artifact_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr("app.services.registry_service.settings.artifacts_dir", tmpdir)
            RegistryService.register_artifact("proj-a", str(sample_artifact_dir))
            result = RegistryService.delete_version("proj-a", "v1")
            assert result["status"] == "deleted"
            versions = RegistryService.list_versions("proj-a")
            assert len(versions) == 0

    def test_get_artifact_path(self, monkeypatch, sample_artifact_dir):
        with tempfile.TemporaryDirectory() as tmpdir:
            monkeypatch.setattr("app.services.registry_service.settings.artifacts_dir", tmpdir)
            RegistryService.register_artifact("proj-a", str(sample_artifact_dir))
            path = RegistryService.get_artifact_path("proj-a", "v1")
            assert path is not None
            assert path.exists()
            assert (path / "manifest.json").exists()
