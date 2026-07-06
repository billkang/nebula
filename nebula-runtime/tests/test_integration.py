"""集成测试 — Runtime 端到端：注册 Artifact → 查询 → 删除 + 错误场景"""
import json
import tarfile
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)


@pytest.fixture
def valid_artifact_tgz():
    """Create a valid artifact tar.gz for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        artifact_dir = Path(tmpdir) / "artifact"
        artifact_dir.mkdir()

        src_dir = artifact_dir / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("from fastapi import FastAPI\napp = FastAPI()\n@app.get('/health')\nasync def h(): return {'status': 'ok'}\n")

        (artifact_dir / "requirements.txt").write_text("fastapi\nuvicorn\n")
        (artifact_dir / "Dockerfile").write_text("FROM python:3.12-slim\nWORKDIR /app\nCOPY . .\nRUN pip install -r requirements.txt\nCMD uvicorn src.main:app --host 0.0.0.0 --port 8000\n")

        # Create tar.gz
        tgz = Path(tmpdir) / "test-artifact.tar.gz"
        with tarfile.open(tgz, "w:gz") as tar:
            for item in ["src", "requirements.txt", "Dockerfile"]:
                path = artifact_dir / item
                if path.exists():
                    tar.add(str(path), arcname=item)

        yield tgz


class TestRuntimeIntegration:

    def test_full_flow_register_and_query(self, valid_artifact_tgz):
        """完整流程：注册 Artifact → 查询 → 删除"""
        project_id = "e2e-proj"

        # 注册
        with open(valid_artifact_tgz, "rb") as f:
            resp = client.post(
                f"/api/v1/registry/artifacts/{project_id}",
                files={"file": ("artifact.tar.gz", f, "application/gzip")},
            )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["version"] == "v1"
        assert data["status"] == "ready"

        # 查询列表
        resp = client.get("/api/v1/registry/artifacts", params={"project_id": project_id})
        assert resp.status_code == 200
        versions = resp.json()["data"]
        assert len(versions) == 1
        assert versions[0]["version"] == "v1"

        # 查询详情
        resp = client.get(f"/api/v1/registry/artifacts/{project_id}/v1")
        assert resp.status_code == 200
        assert resp.json()["data"]["version"] == "v1"

        # 删除
        resp = client.delete(f"/api/v1/registry/artifacts/{project_id}/v1")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "deleted"

    def test_register_invalid_tar(self):
        """注册非法文件应返回错误"""
        resp = client.post(
            "/api/v1/registry/artifacts/bad-proj",
            files={"file": ("bad.tar.gz", b"not-a-tar-gz", "application/gzip")},
        )
        assert resp.status_code == 400

    def test_register_version_autoincrement(self, valid_artifact_tgz):
        """连续注册自动递增版本号"""
        project_id = "e2e-increment"

        for expected in ["v1", "v2", "v3"]:
            with open(valid_artifact_tgz, "rb") as f:
                resp = client.post(
                    f"/api/v1/registry/artifacts/{project_id}",
                    files={"file": ("artifact.tar.gz", f, "application/gzip")},
                )
            assert resp.status_code == 200
            assert resp.json()["data"]["version"] == expected

    def test_runtime_push_endpoint(self, valid_artifact_tgz):
        """runtime push 端点正常工作"""
        project_id = "e2e-push"

        # Register first so there's a version
        with open(valid_artifact_tgz, "rb") as f:
            resp = client.post(
                f"/api/v1/registry/artifacts/{project_id}",
                files={"file": ("artifact.tar.gz", f, "application/gzip")},
            )
        assert resp.status_code == 200

        # Test runtime start with nonexistent version
        resp = client.post(
            "/api/v1/runtime/start",
            json={"project_id": project_id, "version": "v999"},
        )
        assert resp.status_code == 404

    def test_runtime_status_idle(self):
        """刚启动时 runtime 状态为 idle"""
        resp = client.get("/api/v1/runtime/status")
        assert resp.status_code == 200
        assert resp.json()["data"]["status"] == "idle"

    def test_health_endpoint(self):
        """health 端点正常"""
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_delete_nonexistent_version(self):
        """删除不存在的版本返回 404"""
        resp = client.delete("/api/v1/registry/artifacts/e2e-nonexistent/v999")
        assert resp.status_code == 404
