"""DocService 单元测试 — 项目 openspec 工作区路径"""
import os
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from app.models.user import User, UserRole
from app.services.auth_service import hash_password
from app.services.doc_service import DocService
from app.utils.project_path import get_projects_base


def _setup_project(client, db, username="doc_user"):
    """辅助：创建测试用户 + 项目，返回 (token, pid)。

    change_name 由 conftest 的 autouse mock 统一设为 test-project。
    """
    user = User(username=username, email=f"{username}@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login",
                       json={"username": username, "password": "pass123"})
    token = resp.json()["access_token"]

    resp = client.post("/api/v1/projects", json={"name": f"{username}项目"},
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    return token, resp.json()["id"]


class TestDocServiceGenerate:
    """generate_docs 生成 SDD 文档到项目 openspec 工作区"""

    def test_generate_docs_writes_conversation_context(self, client, db):
        """generate_docs 将 conversation_context.md 写入项目根目录。"""
        token, pid = _setup_project(client, db, "genctx")
        project_dir = get_projects_base() / "genctx-test-project"

        assert not (project_dir / "conversation_context.md").exists()

        with patch("app.services.doc_service.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"instruction": "test", "template": "test", "outputPath": "test.md"}'
            result = DocService.generate_docs(
                project_id=pid, db=db,
                req_summary="用户管理系统",
                out_of_scope=["部署", "监控"],
            )

        assert result["success"] is True
        assert (project_dir / "conversation_context.md").exists()
        content = (project_dir / "conversation_context.md").read_text(encoding="utf-8")
        assert "用户管理系统" in content
        assert "Out of Scope" in content
        assert "部署" in content

    def test_generate_docs_no_out_of_scope_section(self, client, db):
        """out_of_scope 为 None 时省略 ## Out of Scope 章节。"""
        token, pid = _setup_project(client, db, "noscope")
        project_dir = get_projects_base() / "noscope-test-project"

        with patch("app.services.doc_service.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 0
            mock_run.return_value.stdout = '{"instruction": "test", "template": "test", "outputPath": "test.md"}'
            result = DocService.generate_docs(
                project_id=pid, db=db,
                req_summary="用户管理系统",
                out_of_scope=None,
            )

        assert result["success"] is True
        assert (project_dir / "conversation_context.md").exists()
        content = (project_dir / "conversation_context.md").read_text(encoding="utf-8")
        assert "Out of Scope" not in content, "out_of_scope=None 时应省略 ## Out of Scope"
        assert "用户管理系统" in content

    def test_generate_docs_openspec_cli_failure(self, client, db):
        """openspec CLI 返回非零退出码时返回错误。"""
        token, pid = _setup_project(client, db, "genfail")

        with patch("app.services.doc_service.subprocess.run") as mock_run:
            mock_run.return_value.returncode = 1
            mock_run.return_value.stderr = "openspec error"
            result = DocService.generate_docs(project_id=pid, db=db)

        assert result["success"] is False
        assert "openspec error" in result["message"]


class TestDocServicePath:
    """DocService 路径解析 — 基于 project_id 查 DB 得到 username + change_name"""

    def test_get_project_dir_returns_correct_path(self, client: TestClient, db):
        """获取项目目录路径为 projects/{username}-{change_name}/。"""
        user = User(username="pathuser", email="pathuser@test.com",
                    password=hash_password("pass123"), role=UserRole.ADMIN)
        db.add(user)
        db.commit()
        resp = client.post("/api/v1/auth/login",
                           json={"username": "pathuser", "password": "pass123"})
        token = resp.json()["access_token"]

        resp = client.post("/api/v1/projects", json={"name": "路径测试"},
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        pid = resp.json()["id"]

        # 通过 DocService 获取项目目录路径
        project_dir = DocService.get_project_dir(pid, db)
        expected = str(get_projects_base() / "pathuser-test-project")
        assert project_dir == expected, f"预期 {expected}，实际 {project_dir}"

    def test_list_docs_from_project_workspace(self, client: TestClient, db):
        """list_docs 从项目 openspec 工作区读取 change 列表。"""
        user = User(username="listdoc", email="listdoc@test.com",
                    password=hash_password("pass123"), role=UserRole.ADMIN)
        db.add(user)
        db.commit()
        resp = client.post("/api/v1/auth/login",
                           json={"username": "listdoc", "password": "pass123"})
        token = resp.json()["access_token"]

        resp = client.post("/api/v1/projects", json={"name": "列表测试"},
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        pid = resp.json()["id"]

        # 项目刚创建，changges 目录为空，应返回空列表
        docs = DocService.list_docs(pid, db)
        assert isinstance(docs, list)

    def test_get_doc_returns_none_for_missing(self, client: TestClient, db):
        """get_doc 在文档不存在时返回 None。"""
        user = User(username="getdoc", email="getdoc@test.com",
                    password=hash_password("pass123"), role=UserRole.ADMIN)
        db.add(user)
        db.commit()
        resp = client.post("/api/v1/auth/login",
                           json={"username": "getdoc", "password": "pass123"})
        token = resp.json()["access_token"]

        resp = client.post("/api/v1/projects", json={"name": "读取测试"},
                           headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200
        pid = resp.json()["id"]

        # 没有生成文档，应返回 None
        content = DocService.get_doc(pid, "proposal", db)
        assert content is None
