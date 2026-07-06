"""集成测试 — 完整链路：注册 → 登录 → 创建项目 → 创建会话 → 发送消息"""
import pytest
from fastapi.testclient import TestClient


def test_full_flow_register_login_project_chat(client: TestClient, db):
    """完整链路：注册 → 登录 → 创建项目 → 创建会话 → 发送消息 → 获取消息"""
    # ── 注册新用户 ──
    resp = client.post("/api/v1/auth/register", json={
        "username": "integration_user",
        "email": "int@test.com",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    user_id = resp.json()["id"]

    # ── 登录 ──
    resp = client.post("/api/v1/auth/login", json={
        "username": "integration_user",
        "password": "testpass123",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    token = data["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ── 获取当前用户信息 ──
    resp = client.get("/api/v1/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["id"] == user_id

    # ── 创建项目 ──
    resp = client.post("/api/v1/projects", json={
        "name": "集成测试项目",
        "description": "用于集成测试",
    }, headers=headers)
    assert resp.status_code == 200
    project = resp.json()
    assert project["name"] == "集成测试项目"
    project_id = project["id"]

    # ── 列出项目 ──
    resp = client.get("/api/v1/projects", headers=headers)
    assert resp.status_code == 200
    assert any(p["id"] == project_id for p in resp.json())

    # ── 项目详情 ──
    resp = client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "集成测试项目"

    # ── 创建会话 ──
    resp = client.post(f"/api/v1/projects/{project_id}/sessions", headers=headers)
    assert resp.status_code == 200
    session = resp.json()
    assert session["project_id"] == project_id
    session_id = session["id"]

    # ── 发送消息 → Agent 处理 ──
    resp = client.post(
        f"/api/v1/projects/{project_id}/sessions/{session_id}/messages",
        json={"content": "我想开发一个博客系统，支持文章发布、分类管理和评论功能，用 Python Flask 实现。"},
        headers=headers,
    )
    assert resp.status_code == 200
    messages = resp.json()
    assert len(messages) >= 1
    # 第一条应该是系统的欢迎消息
    first = messages[0]
    assert first["role"] in ("agent", "user")

    # ── 获取消息历史 ──
    resp = client.get(
        f"/api/v1/projects/{project_id}/sessions/{session_id}/messages",
        headers=headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == len(messages)


def test_full_flow_with_admin_delete(client: TestClient, db):
    """admin 用户可以删除项目"""
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password

    admin = User(username="int_admin", email="int_admin@test.com",
                 password=hash_password("admin123"), role=UserRole.ADMIN)
    db.add(admin)
    db.commit()

    resp = client.post("/api/v1/auth/login",
                       json={"username": "int_admin", "password": "admin123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 创建项目
    resp = client.post("/api/v1/projects", json={"name": "待删除项目"},
                       headers=headers)
    pid = resp.json()["id"]

    # admin 可以删除
    resp = client.delete(f"/api/v1/projects/{pid}", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["message"] == "项目已删除"


def test_member_cannot_delete(client: TestClient, db):
    """member 用户删除项目应返回 403"""
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password

    member = User(username="int_member", email="int_member@test.com",
                  password=hash_password("member123"), role=UserRole.MEMBER)
    db.add(member)
    db.commit()

    resp = client.post("/api/v1/auth/login",
                       json={"username": "int_member", "password": "member123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    resp = client.delete("/api/v1/projects/nonexistent-id", headers=headers)
    assert resp.status_code == 403


def test_docs_generate_execute_build_flow(client: TestClient, db):
    """文档生成 → 编码执行 → 构建验证的 API 状态流转"""
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password

    admin = User(username="flow_admin", email="flow_admin@test.com",
                 password=hash_password("flow123"), role=UserRole.ADMIN)
    db.add(admin)
    db.commit()

    resp = client.post("/api/v1/auth/login",
                       json={"username": "flow_admin", "password": "flow123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # ── 创建项目 ──
    resp = client.post("/api/v1/projects", json={"name": "全链路项目"},
                       headers=headers)
    assert resp.status_code == 200
    pid = resp.json()["id"]

    # ── 查看文档列表（初始状态） ──
    resp = client.get(f"/api/v1/projects/{pid}/docs", headers=headers)
    assert resp.status_code == 200
    docs = resp.json()
    assert isinstance(docs, list)
    # 文档可能不存在，但应返回列表结构
    assert all("type" in d and "exists" in d for d in docs)

    # ── 获取执行状态（初始 idle） ──
    resp = client.get(f"/api/v1/projects/{pid}/execute/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "idle"

    # ── 获取构建状态（初始 idle） ──
    resp = client.get(f"/api/v1/projects/{pid}/build/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "idle"

    # ── 获取 artifact 列表（初始空） ──
    resp = client.get(f"/api/v1/projects/{pid}/build/artifacts", headers=headers)
    assert resp.status_code == 200
    assert resp.json() == []


def test_docs_list_with_session_context(client: TestClient, db):
    """文档列表接口在有 session agent state 时返回正常"""
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password

    admin = User(username="doc_admin", email="doc_admin@test.com",
                 password=hash_password("doc123"), role=UserRole.ADMIN)
    db.add(admin)
    db.commit()

    resp = client.post("/api/v1/auth/login",
                       json={"username": "doc_admin", "password": "doc123"})
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 创建项目 + 会话
    resp = client.post("/api/v1/projects", json={"name": "文档项目"},
                       headers=headers)
    pid = resp.json()["id"]

    resp = client.post(f"/api/v1/projects/{pid}/sessions", headers=headers)
    assert resp.status_code == 200
    sid = resp.json()["id"]

    # 发送消息触发 agent state
    resp = client.post(
        f"/api/v1/projects/{pid}/sessions/{sid}/messages",
        json={"content": "我想开发一个用户管理系统，包含注册、登录和权限管理功能，用 FastAPI 实现。"},
        headers=headers,
    )
    assert resp.status_code == 200

    # 文档列表正常
    resp = client.get(f"/api/v1/projects/{pid}/docs", headers=headers)
    assert resp.status_code == 200

    # 获取指定类型文档（可能不存在，返回 404）
    resp = client.get(f"/api/v1/projects/{pid}/docs/nonexistent", headers=headers)
    assert resp.status_code == 404
