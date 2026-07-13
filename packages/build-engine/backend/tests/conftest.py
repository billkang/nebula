from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.services.auth_service import hash_password
from app.config import settings

# 测试环境 - mock LLM 翻译，避免真实 API 调用
settings.llm_api_key = "sk-test-key-for-testing"
settings.llm_provider = "deepseek"

# 测试项目目录与正式 projects/ 隔离，互不影响
settings.projects_dir = "projects_test"


@pytest.fixture(autouse=True)
def _mock_translate_change_name():
    """全局 mock translate_change_name，所有 API 调用自动返回固定 change_name。"""
    from unittest.mock import patch
    with patch("app.services.project_service.translate_change_name",
               return_value="test-project"):
        yield


@pytest.fixture(autouse=True)
def _cleanup_projects_dir():
    """每次测试完成后清理 projects_test/ 目录，不影响正式 projects/。"""
    projects_dir = Path(__file__).parent.parent / settings.projects_dir
    before = {p.name for p in projects_dir.iterdir()} if projects_dir.exists() else set()
    yield
    if projects_dir.exists():
        import shutil
        for item in list(projects_dir.iterdir()):
            if item.is_dir() and item.name not in before:
                shutil.rmtree(item, ignore_errors=True)


TEST_DB_URL = "sqlite:///./test_nebula.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def db():
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
