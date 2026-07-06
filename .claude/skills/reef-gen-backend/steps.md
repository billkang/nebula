# Python 后端编码步骤（FastAPI）

按以下顺序逐块编写，依赖关系由前向后：

## 0. 安装依赖

如项目尚未安装所需包，用 `uv` 安装：

```bash
# FastAPI + ASGI 服务器
uv add fastapi uvicorn[standard]

# SQLAlchemy（异步）+ Alembic
uv add sqlalchemy[asyncio] alembic asyncpg

# Pydantic 验证
uv add pydantic[email]

# LangChain（如启用 AI 集成）
uv add langchain langchain-openai

# 开发依赖
uv add --dev pytest pytest-asyncio httpx ruff mypy
```

1. **Schema** — Pydantic Model，定义请求/响应结构
2. **Model** — SQLAlchemy ORM Model，定义表结构
3. **Migration** — Alembic 迁移文件，生成 DDL
4. **Service** — 业务逻辑，输入验证，事务管理
5. **Router** — FastAPI API 路由，请求/响应
6. **注册到主应用**

将新创建的路由器注册到主应用中：

```python
# app/main.py
from fastapi import FastAPI
from app.api.v1 import users, orders

app = FastAPI(title="MyApp")

# 注册路由
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])
app.include_router(orders.router, prefix="/api/v1/orders", tags=["orders"])
```

每完成一块对照 `reef:reef-style-backend` 的 Python 章节检查。

## ⚠️ 异步红线

- 所有数据库操作用 `AsyncSession`，禁止同步 `Session`
- Service 层函数都用 `async def`
- `async def` 内部禁止调同步 IO（`time.sleep()`、`requests.get()`）
- 需要同步操作时用 `asyncio.to_thread()` 包裹

## 构建命令

```bash
# 格式化和 lint
ruff check . && ruff format

# 类型检查
mypy .

# 运行测试
python -m pytest

# 启动开发服务器
uv run uvicorn app.main:app --reload
```
