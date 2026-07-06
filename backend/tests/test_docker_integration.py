"""Integration tests for DockerCoderBackend. Requires a running Docker daemon."""

import pytest


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

    def test_builder_container_runs(self, tmp_path):
        """Run the builder container on a minimal test project."""
        # Create a minimal project structure
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "main.py").write_text("print('hello')")
        (tmp_path / "requirements.txt").write_text("")
        (tmp_path / "Dockerfile").write_text("FROM python:3.12-slim\nCMD [\"python\", \"src/main.py\"]")

        from app.services.backends.docker_backend import DockerCoderBackend
        backend = DockerCoderBackend()
        result = backend.execute_build(str(tmp_path))

        assert result.status == "success"
        assert result.artifact_path is not None
        assert result.artifact_path.endswith("artifact.tar.gz")

        # Verify artifacts created on host
        assert (tmp_path / "artifacts" / "artifact.tar.gz").exists()
        assert (tmp_path / "artifacts" / "manifest.json").exists()
