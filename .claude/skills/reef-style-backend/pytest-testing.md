# pytest 测试规范

## 目录结构

```
tests/
├── conftest.py           # 全局 fixture
├── unit/                 # 纯逻辑单元测试
│   ├── test_services/
│   └── test_schemas/
└── integration/          # 集成测试（DB / API）
    ├── test_api/
    └── conftest.py       # 集成测试专用 fixture
```

**规范：**
- `tests/unit/` — 不依赖外部服务的纯逻辑测试
- `tests/integration/` — 依赖数据库、HTTP 调用的测试
- 测试文件以 `test_` 开头，函数以 `test_` 开头

## pytest fixture

```python
# ✅ 好：conftest.py 中的共享 fixture
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession

@pytest_asyncio.fixture
async def db_session():
    # 每个测试独立事务，测试后回滚
    async with async_session() as session:
        async with session.begin():
            yield session
        await session.rollback()

@pytest_asyncio.fixture
async def user_service(db_session: AsyncSession):
    return UserService(db=db_session)
```

**规范：**
- 测试用 `pytest-asyncio` 支持异步 fixture 和 test
- fixture 只在 `conftest.py` 中定义，不在测试文件中
- fixture 范围默认 `function`，仅共享资源用 `session` / `module`

## 异步测试

```python
# ✅ 好：pytest-asyncio 异步测试
import pytest

@pytest.mark.asyncio
async def test_create_user(user_service: UserService):
    user = await user_service.create_user(name="Alice", email="alice@example.com")
    assert user.id is not None
    assert user.name == "Alice"
```

## 集成测试标记

```python
import pytest

# ✅ 好：用 mark 区分测试类型
@pytest.mark.integration
@pytest.mark.asyncio
async def test_api_list_users(client: httpx.AsyncClient):
    response = await client.get("/api/v1/users")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
```

## HTTP 测试

```python
# ✅ 好：用 httpx AsyncClient 配合 FastAPI TestClient
from httpx import AsyncClient, ASGITransport

@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_get_user(client: AsyncClient):
    response = await client.get("/api/v1/users/1")
    assert response.status_code == 200
    assert response.json()["id"] == 1
```

## 运行命令

```bash
# 运行全部测试
python -m pytest

# 指定目录
python -m pytest tests/unit/

# 包含覆盖率
python -m pytest --cov=app --cov-report=term-missing

# 仅集成测试
python -m pytest -m integration

# 并行运行
python -m pytest -n auto
```
