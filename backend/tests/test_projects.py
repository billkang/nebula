def test_create_project(client, db):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="projuser", email="proj@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "projuser", "password": "pass123"})
    token = resp.json()["access_token"]

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
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="deluser", email="del@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "deluser", "password": "pass123"})
    token = resp.json()["access_token"]

    create = client.post("/api/v1/projects", json={"name": "待删除"},
                         headers={"Authorization": f"Bearer {token}"})
    pid = create.json()["id"]
    resp = client.delete(f"/api/v1/projects/{pid}",
                         headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
