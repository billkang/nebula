import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


class TestHealth:
    def test_health_endpoint(self):
        resp = client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


class TestRegistryAPI:
    def test_list_versions_empty(self):
        resp = client.get("/api/v1/registry/artifacts", params={"project_id": "nonexistent"})
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data == []

    def test_get_version_not_found(self):
        resp = client.get("/api/v1/registry/artifacts/nonexistent/v1")
        assert resp.status_code == 404

    def test_delete_nonexistent(self):
        resp = client.delete("/api/v1/registry/artifacts/nonexistent/v1")
        assert resp.status_code == 404


class TestRuntimeAPI:
    def test_status_idle(self):
        resp = client.get("/api/v1/runtime/status")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "idle"

    def test_stop_when_idle(self):
        resp = client.post("/api/v1/runtime/stop")
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] in ("stopped", "idle")

    def test_start_artifact_not_found(self):
        resp = client.post(
            "/api/v1/runtime/start",
            json={"project_id": "nonexistent", "version": "v1"},
        )
        assert resp.status_code == 404

    def test_logs_when_idle(self):
        resp = client.get("/api/v1/runtime/logs")
        assert resp.status_code == 200
        assert resp.json()["data"] == ""
