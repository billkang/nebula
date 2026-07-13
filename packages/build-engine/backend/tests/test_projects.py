def test_create_project(client, db):
    from unittest.mock import patch
    from app.models.user import User, UserRole
    from app.utils.project_path import get_projects_base
    from app.services.auth_service import hash_password
    user = User(username="projuser", email="proj@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "projuser", "password": "pass123"})
    token = resp.json()["access_token"]

    with patch("app.services.project_service.translate_change_name", return_value="my-project"):
        resp = client.post("/api/v1/projects", json={"name": "我的项目", "description": "测试"},
                           headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["name"] == "我的项目"


def test_list_projects_empty(client, db):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="listuser", email="list@test.com",
                password=hash_password("pass123"), role=UserRole.MEMBER)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "listuser", "password": "pass123"})
    token = resp.json()["access_token"]

    resp = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token}"})
    assert resp.json() == []


def test_delete_project(client, db):
    from unittest.mock import patch
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="deluser", email="del@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "deluser", "password": "pass123"})
    token = resp.json()["access_token"]

    with patch("app.services.project_service.translate_change_name", return_value="to-delete"):
        create = client.post("/api/v1/projects", json={"name": "待删除"},
                             headers={"Authorization": f"Bearer {token}"})
    pid = create.json()["id"]
    resp = client.delete(f"/api/v1/projects/{pid}",
                         headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


# ===== change_name 翻译集成 =====

def test_create_project_returns_change_name(client, db):
    """创建项目时返回翻译后的 change_name。"""
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="cn_user", email="cn@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "cn_user", "password": "pass123"})
    token = resp.json()["access_token"]

    # mock 翻译函数（通过 patch translate_change_name）
    from unittest.mock import patch
    with patch("app.services.project_service.translate_change_name", return_value="travel-assistant"):
        resp = client.post("/api/v1/projects", json={"name": "旅游助手"},
                           headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["change_name"] == "travel-assistant"
    assert data["name"] == "旅游助手"


def test_create_project_has_openspec_workspace(client, db):
    """创建项目后，项目目录中有 openspec 工作区结构。"""
    from app.utils.project_path import get_projects_base
    from pathlib import Path
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="specuser", email="specuser@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "specuser", "password": "pass123"})
    token = resp.json()["access_token"]

    from unittest.mock import patch
    with patch("app.services.project_service.translate_change_name", return_value="spec-test"):
        resp = client.post("/api/v1/projects", json={"name": "Spec测试"},
                           headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # 验证项目目录和 openspec 工作区结构
    project_dir = get_projects_base() / "specuser-spec-test"
    assert project_dir.exists()
    assert (project_dir / "openspec").exists(), "缺少 openspec/ 目录"
    assert (project_dir / "openspec" / "changes").exists(), "缺少 openspec/changes/"
    assert (project_dir / "openspec" / "specs").exists(), "缺少 openspec/specs/"
    assert (project_dir / "openspec" / "changes" / "archive").exists(), "缺少 openspec/changes/archive/"


def test_delete_project_removes_directory(client, db):
    """删除项目时清理文件系统目录。"""
    from app.utils.project_path import get_projects_base
    from pathlib import Path
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="deluser2", email="deluser2@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "deluser2", "password": "pass123"})
    token = resp.json()["access_token"]

    from unittest.mock import patch
    with patch("app.services.project_service.translate_change_name", return_value="del-test"):
        create = client.post("/api/v1/projects", json={"name": "删除测试"},
                             headers={"Authorization": f"Bearer {token}"})
    assert create.status_code == 200
    pid = create.json()["id"]

    project_dir = get_projects_base() / "deluser2-del-test"
    assert project_dir.exists(), "项目目录应在删除前存在"

    resp = client.delete(f"/api/v1/projects/{pid}",
                         headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200

    # 验证目录被清理
    assert not project_dir.exists(), "项目目录应在删除后被清理"


def test_delete_project_missing_directory_succeeds(client, db):
    """删除项目时如果目录已不存在，不应阻塞 DB 删除。"""
    from app.utils.project_path import get_projects_base
    from pathlib import Path
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="deluser3", email="deluser3@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "deluser3", "password": "pass123"})
    token = resp.json()["access_token"]

    from unittest.mock import patch
    with patch("app.services.project_service.translate_change_name", return_value="del-missing"):
        create = client.post("/api/v1/projects", json={"name": "缺失目录"},
                             headers={"Authorization": f"Bearer {token}"})
    assert create.status_code == 200
    pid = create.json()["id"]

    # 手动删除目录
    project_dir = get_projects_base() / "deluser3-del-missing"
    import shutil
    shutil.rmtree(project_dir, ignore_errors=True)
    assert not project_dir.exists(), "测试前提：目录已被手动删除"

    # 删除项目应仍然成功
    resp = client.delete(f"/api/v1/projects/{pid}",
                         headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200


def test_project_id_is_string(client, db):
    """创建项目后返回的 id 应为 str (UUID)。"""
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="id_str_user", email="idstr@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "id_str_user", "password": "pass123"})
    token = resp.json()["access_token"]

    from unittest.mock import patch
    with patch("app.services.project_service.translate_change_name", return_value="id-test"):
        resp = client.post("/api/v1/projects", json={"name": "ID测试"},
                           headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data["id"], str), f"Expected str id, got {type(data['id'])}: {data['id']}"
    assert len(data["id"]) > 0


# ===== 获取单个项目 =====

def test_get_project_by_id(client, db):
    """获取单个项目详情。"""
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="getuser", email="getuser@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "getuser", "password": "pass123"})
    token = resp.json()["access_token"]

    from unittest.mock import patch
    with patch("app.services.project_service.translate_change_name", return_value="get-test"):
        create = client.post("/api/v1/projects", json={"name": "获取测试", "description": "描述"},
                             headers={"Authorization": f"Bearer {token}"})
    assert create.status_code == 200
    pid = create.json()["id"]

    resp = client.get(f"/api/v1/projects/{pid}",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert data["id"] == pid
    assert data["name"] == "获取测试"
    assert data["description"] == "描述"


def test_get_project_not_found(client, db):
    """获取不存在的项目返回 404。"""
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="get404", email="get404@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "get404", "password": "pass123"})
    token = resp.json()["access_token"]

    resp = client.get("/api/v1/projects/999999",
                      headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 404


def test_get_project_unauthorized(client):
    """未登录时获取项目返回 401。"""
    resp = client.get("/api/v1/projects/some-id")
    assert resp.status_code == 401


def test_create_project_unauthorized(client):
    """未登录时创建项目返回 401。"""
    resp = client.post("/api/v1/projects", json={"name": "测试"})
    assert resp.status_code == 401


def test_create_project_empty_name(client, db):
    """创建项目时空名称返回 422。"""
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="emptyuser", email="empty@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "emptyuser", "password": "pass123"})
    token = resp.json()["access_token"]

    resp = client.post("/api/v1/projects", json={"name": ""},
                       headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 422


def test_list_projects_returns_change_name(client, db):
    """项目列表也包含 change_name。"""
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="list_cn", email="listcn@test.com",
                password=hash_password("pass123"), role=UserRole.MEMBER)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "list_cn", "password": "pass123"})
    token = resp.json()["access_token"]

    from unittest.mock import patch
    with patch("app.services.project_service.translate_change_name", return_value="data-platform"):
        client.post("/api/v1/projects", json={"name": "数据平台"},
                    headers={"Authorization": f"Bearer {token}"})

    resp = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["change_name"] == "data-platform"
