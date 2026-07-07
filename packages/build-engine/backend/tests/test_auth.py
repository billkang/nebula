import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from app.services.auth_service import hash_password, verify_password
from app.middleware.auth import get_current_user_sse
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


# ── RED test: get_current_user_sse 尚未实现 ──


def test_get_current_user_sse_import():
    """RED: get_current_user_sse 仅实现后可通过导入测试。"""
    from app.middleware.auth import get_current_user_sse
    assert callable(get_current_user_sse)


# ── GREEN test: 实现后这些集成测试应该通过 ──


def test_sse_auth_token_query_param(db):
    """SSE auth via token query param should succeed.

    Uses the test app from test_sse_auth_authorization_header which
    tests get_current_user_sse in isolation, avoiding the SSE streaming
    response that would hang in httpx.ASGITransport.
    """
    from jose import jwt
    from app.config import settings

    user = User(username="ssetest", email="sse@test.com",
                password=hash_password("test123456"), role=UserRole.MEMBER)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = jwt.encode({"sub": str(user.id)}, settings.jwt_secret, algorithm="HS256")
    # _test_client is defined below (after _override_get_db), but module-level
    # code executes top-to-bottom before any test function is called
    resp = _test_client.get("/_test_auth", params={"token": token})
    assert resp.status_code == 200
    assert resp.json()["user_id"] == str(user.id)


def test_sse_auth_no_token_fails():
    """SSE auth without any token should fail."""
    resp = _test_client.get("/_test_auth")
    assert resp.status_code == 401


# ── Authorization header fallback for get_current_user_sse ──


from app.database import get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

_test_engine = create_engine("sqlite:///./test_nebula.db", connect_args={"check_same_thread": False})
_TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_test_engine)


def _override_get_db():
    db = _TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


_test_app = FastAPI()
_test_app.dependency_overrides[get_db] = _override_get_db


@_test_app.get("/_test_auth")
async def _test_auth(user=Depends(get_current_user_sse)):
    return {"user_id": user.id}


_test_client = TestClient(_test_app)


def test_sse_auth_authorization_header(db):
    """Authorization header fallback should work for get_current_user_sse."""
    from jose import jwt
    from app.config import settings

    user = User(username="authheader", email="authheader@test.com",
                password=hash_password("test123456"), role=UserRole.MEMBER)
    db.add(user)
    db.commit()
    db.refresh(user)

    token = jwt.encode({"sub": str(user.id)}, settings.jwt_secret, algorithm="HS256")

    # Test with Authorization header
    resp = _test_client.get("/_test_auth", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
    assert resp.json()["user_id"] == str(user.id)

    # Test without any auth
    resp2 = _test_client.get("/_test_auth")
    assert resp2.status_code == 401
