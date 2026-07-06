from app.services.auth_service import hash_password, verify_password
from app.models.user import User, UserRole


def test_password_hashing():
    hashed = hash_password("testpass")
    assert verify_password("testpass", hashed)
    assert not verify_password("wrongpass", hashed)


def test_register(client):
    resp = client.post("/api/v1/auth/register", json={
        "username": "newuser",
        "email": "new@test.com",
        "password": "test123456",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "newuser"
    assert data["role"] == "member"


def test_register_duplicate_email(client):
    client.post("/api/v1/auth/register", json={
        "username": "user1", "email": "dup@test.com", "password": "test123456"
    })
    resp = client.post("/api/v1/auth/register", json={
        "username": "user2", "email": "dup@test.com", "password": "test123456"
    })
    assert resp.status_code == 400


def test_login_success(client, db):
    user = User(username="loginuser", email="login@test.com",
                password=hash_password("pass123"), role=UserRole.MEMBER)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "loginuser", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()


def test_login_wrong_password(client, db):
    user = User(username="loginfail", email="fail@test.com",
                password=hash_password("correct"), role=UserRole.MEMBER)
    db.add(user)
    db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "loginfail", "password": "wrong"})
    assert resp.status_code == 401
