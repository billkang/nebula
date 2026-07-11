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


@pytest.fixture(autouse=True)
def _mock_translate_change_name():
    """全局 mock translate_change_name，所有 API 调用自动返回固定 change_name。"""
    from unittest.mock import patch
    with patch("app.services.project_service.translate_change_name",
               return_value="test-project"):
        yield

@pytest.fixture(autouse=True)
def _cleanup_projects_dir(request):
    """每次测试完成后清理 projects/ 下的测试目录。"""
    yield
    projects_dir = Path(__file__).parent.parent / "projects"
    if projects_dir.exists():
        import shutil
        for item in projects_dir.iterdir():
            if item.is_dir():
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
