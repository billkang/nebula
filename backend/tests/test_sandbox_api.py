"""Sandbox API 集成测试"""
import json, shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from app.services.build_service import BuildService

BASE_DIR = Path(__file__).resolve().parent.parent.parent


def _setup_project_with_artifact(client: TestClient, headers: dict, project_name: str):
    """创建项目并准备一个 Artifact。"""
    # 创建项目
    resp = client.post("/api/v1/projects", json={"name": project_name}, headers=headers)
    assert resp.status_code == 200
    pid = resp.json()["id"]

    # 手动创建项目文件结构（模拟构建完成的状态）
    project_dir = BASE_DIR / "projects" / pid
    (project_dir / "src").mkdir(parents=True, exist_ok=True)
    (project_dir / "src" / "main.py").write_text(
        "print('hello from sandbox test')\n", encoding="utf-8"
    )
    (project_dir / "src" / "utils.py").write_text(
        "def util():\n    return 'ok'\n", encoding="utf-8"
    )
    # 添加测试让 pytest 通过
    (project_dir / "tests").mkdir(exist_ok=True)
    (project_dir / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (project_dir / "tests" / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8"
    )
    (project_dir / "requirements.txt").write_text("pytest\n", encoding="utf-8")
    (project_dir / "Dockerfile").write_text("FROM python:3.12-slim\n", encoding="utf-8")

    # 生成一个 Artifact（手动创建，不依赖 BuildService Docker backend）
    import tarfile, json
    from datetime import datetime, timezone
    artifact_version = "v1"

    from app.services.build_service import _build_states
    _build_states.clear()

    artifact_dir = project_dir / "artifacts" / artifact_version
    artifact_dir.mkdir(parents=True, exist_ok=True)

    manifest = {
        "version": artifact_version,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "entry": "src/main.py",
        "dependencies": ["pytest"],
    }
    with open(artifact_dir / "manifest.json", "w") as f:
        json.dump(manifest, f)

    tar_path = artifact_dir / "artifact.tar.gz"
    with tarfile.open(tar_path, "w:gz") as tar:
        tar.add(project_dir / "src", arcname="src")
        tar.add(project_dir / "requirements.txt", arcname="requirements.txt")
        tar.add(project_dir / "Dockerfile", arcname="Dockerfile")
        tar.add(artifact_dir / "manifest.json", arcname="manifest.json")

    _build_states[pid] = {
        "status": "success",
        "message": f"构建完成，Artifact: {tar_path}",
        "artifact_version": artifact_version,
        "runtime_status": "runtime_unavailable",
    }

    return pid, artifact_version


class TestSandboxAPI:

    @pytest.fixture(autouse=True)
    def cleanup(self):
        """测试后清理。"""
        yield
        projects_dir = BASE_DIR / "projects"
        if projects_dir.exists():
            for proj in projects_dir.iterdir():
                if proj.is_dir():
                    for sub in ["sandbox", "sandbox_snapshots", "artifacts"]:
                        p = proj / sub
                        if p.exists():
                            shutil.rmtree(p)
        from app.services.build_service import _build_states
        _build_states.clear()

    def _auth_headers(self, client, db):
        """注册并登录返回 headers。"""
        resp = client.post("/api/v1/auth/register", json={
            "username": "sandbox_user",
            "email": "sandbox@test.com",
            "password": "test123",
        })
        assert resp.status_code == 200

        resp = client.post("/api/v1/auth/login", json={
            "username": "sandbox_user",
            "password": "test123",
        })
        token = resp.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def test_init_sandbox_api(self, client: TestClient, db):
        """POST /sandbox/init 初始化沙箱。"""
        headers = self._auth_headers(client, db)
        pid, version = _setup_project_with_artifact(client, headers, "Sandbox Init Test")

        resp = client.post(f"/api/v1/projects/{pid}/sandbox/init", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["initialized"] is True

    def test_init_sandbox_invalid_project(self, client: TestClient, db):
        """不存在的项目 ID 应返回 400。"""
        headers = self._auth_headers(client, db)

        resp = client.post("/api/v1/projects/nonexistent/sandbox/init", headers=headers)
        assert resp.status_code == 400

    def test_get_files_api(self, client: TestClient, db):
        """GET /sandbox/files 返回文件树。"""
        headers = self._auth_headers(client, db)
        pid, version = _setup_project_with_artifact(client, headers, "Sandbox Files Test")

        # 先初始化
        client.post(f"/api/v1/projects/{pid}/sandbox/init", headers=headers)

        resp = client.get(f"/api/v1/projects/{pid}/sandbox/files", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "files" in data
        assert "meta" in data
        # 至少应该有 src/main.py
        assert len(data["files"]) > 0

    def test_get_file_content_api(self, client: TestClient, db):
        """GET /sandbox/files/* 读取文件内容。"""
        headers = self._auth_headers(client, db)
        pid, version = _setup_project_with_artifact(client, headers, "Sandbox Get File")

        client.post(f"/api/v1/projects/{pid}/sandbox/init", headers=headers)

        resp = client.get(f"/api/v1/projects/{pid}/sandbox/files/src/main.py", headers=headers)
        assert resp.status_code == 200
        assert "hello from sandbox" in resp.json()["data"]["content"]

    def test_save_file_api(self, client: TestClient, db):
        """PUT /sandbox/files/* 保存文件。"""
        headers = self._auth_headers(client, db)
        pid, version = _setup_project_with_artifact(client, headers, "Sandbox Save File")

        client.post(f"/api/v1/projects/{pid}/sandbox/init", headers=headers)

        resp = client.put(
            f"/api/v1/projects/{pid}/sandbox/files/src/main.py",
            json={"content": "# modified via API\n"},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["saved"] is True
        assert resp.json()["data"]["modified"] is True

    def test_diff_api(self, client: TestClient, db):
        """GET /sandbox/diff/* 返回 diff。"""
        headers = self._auth_headers(client, db)
        pid, version = _setup_project_with_artifact(client, headers, "Sandbox Diff")

        client.post(f"/api/v1/projects/{pid}/sandbox/init", headers=headers)

        # 修改文件
        client.put(
            f"/api/v1/projects/{pid}/sandbox/files/src/main.py",
            json={"content": "# changed\nprint('diff test')\n"},
            headers=headers,
        )

        resp = client.get(f"/api/v1/projects/{pid}/sandbox/diff/src/main.py", headers=headers)
        assert resp.status_code == 200
        diff_data = resp.json()["data"]
        assert diff_data["has_diff"] is True
        assert diff_data["additions"] >= 1

    def test_snapshot_flow(self, client: TestClient, db):
        """快照创建和列裴。"""
        headers = self._auth_headers(client, db)
        pid, version = _setup_project_with_artifact(client, headers, "Sandbox Snapshots")

        client.post(f"/api/v1/projects/{pid}/sandbox/init", headers=headers)

        # 创建快照
        resp = client.post(
            f"/api/v1/projects/{pid}/sandbox/snapshots",
            json={"description": "API 测试快照"},
            headers=headers,
        )
        assert resp.status_code == 200
        snap_id = resp.json()["data"]["snapshot_id"]

        # 列裴快照
        resp = client.get(f"/api/v1/projects/{pid}/sandbox/snapshots", headers=headers)
        assert resp.status_code == 200
        snapshots = resp.json()["data"]
        assert len(snapshots) >= 1
        assert any(s["snapshot_id"] == snap_id for s in snapshots)

    def test_restore_snapshot_api(self, client: TestClient, db):
        """从快照恢复。"""
        headers = self._auth_headers(client, db)
        pid, version = _setup_project_with_artifact(client, headers, "Sandbox Restore")

        client.post(f"/api/v1/projects/{pid}/sandbox/init", headers=headers)

        # 修改 + 创建快照
        client.put(
            f"/api/v1/projects/{pid}/sandbox/files/src/main.py",
            json={"content": "# snapshot state\n"},
            headers=headers,
        )
        resp = client.post(
            f"/api/v1/projects/{pid}/sandbox/snapshots",
            json={"description": "保存点"},
            headers=headers,
        )
        snap_id = resp.json()["data"]["snapshot_id"]

        # 再次修改
        client.put(
            f"/api/v1/projects/{pid}/sandbox/files/src/main.py",
            json={"content": "# newer state\n"},
            headers=headers,
        )

        # 恢复
        resp = client.post(
            f"/api/v1/projects/{pid}/sandbox/restore/{snap_id}",
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["restored_from"] == snap_id

        # 验证恢复后的内容
        resp = client.get(f"/api/v1/projects/{pid}/sandbox/files/src/main.py", headers=headers)
        assert resp.json()["data"]["content"] == "# snapshot state\n"

    def test_rebuild_api(self, client: TestClient, db):
        """POST /sandbox/rebuild 触发重建。"""
        from app.services.build_service import _build_states
        _build_states.clear()

        headers = self._auth_headers(client, db)
        pid, version = _setup_project_with_artifact(client, headers, "Sandbox Rebuild")

        client.post(f"/api/v1/projects/{pid}/sandbox/init", headers=headers)

        resp = client.post(
            f"/api/v1/projects/{pid}/sandbox/rebuild",
            json={"description": "重建测试"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "snapshot_id" in data

    def test_restore_original_api(self, client: TestClient, db):
        """POST /sandbox/restore-original 恢复原始文件。"""
        headers = self._auth_headers(client, db)
        pid, version = _setup_project_with_artifact(client, headers, "Sandbox RestoreOrig")

        client.post(f"/api/v1/projects/{pid}/sandbox/init", headers=headers)

        # 修改文件
        client.put(
            f"/api/v1/projects/{pid}/sandbox/files/src/main.py",
            json={"content": "# modified\n"},
            headers=headers,
        )

        # 恢复全部
        resp = client.post(
            f"/api/v1/projects/{pid}/sandbox/restore-original",
            json={},
            headers=headers,
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["restored"] is True

        # 验证恢复后内容
        resp = client.get(f"/api/v1/projects/{pid}/sandbox/files/src/main.py", headers=headers)
        assert resp.status_code == 200, f"恢复后读取文件失败: {resp.text}"
        assert "hello from sandbox" in resp.json()["data"]["content"]
