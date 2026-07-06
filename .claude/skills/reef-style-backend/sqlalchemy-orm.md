# SQLAlchemy ORM 使用规范（v2.0+）

## 异步会话管理

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

# ✅ 好：异步引擎 + sessionmaker
engine = create_async_engine(
    "postgresql+asyncpg://user:pass@localhost/db",
    echo=False,
    pool_size=10,
    max_overflow=20,
)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


# ✅ 好：在 Service 中作为依赖
class UserService:
    def __init__(self, db: AsyncSession = Depends(get_async_session)):
        self.db = db

    async def get_user(self, user_id: int) -> User | None:
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
```

**规范：**
- **强制**使用 `AsyncSession` + `async_sessionmaker`
- 禁止同步 `Session` 或 `scoped_session`
- `expire_on_commit=False` 避免 commit 后属性不可访问
- 不要在 Router 中直接操作 `db`，放到 Service 层

## 模型定义（v2.0 style）

```python
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, func

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
```

**规范：**
- **强制**使用 `Mapped` + `mapped_column`（v2.0 style）
- 禁止旧版 `Column`(name, Type) 写法
- 所有模型继承共享 `Base`
- 必要字段声明 `nullable=False`

## 关联关系预加载（防 N+1）

```python
from sqlalchemy.orm import selectinload, joinedload

# ✅ 好：selectinload 预加载
stmt = select(Post).options(selectinload(Post.author)).where(Post.published == True)
result = await db.execute(stmt)

# ✅ 好：joinedload 用于单条查询
stmt = select(Post).options(joinedload(Post.author)).where(Post.id == post_id)
```

**规范：**
- 批量列表查询用 `selectinload()`（发出额外 IN 查询，对列表友好）
- 单条查询用 `joinedload()`（JOIN 一次）
- **禁止**在循环中逐条访问关联属性

## 查询最佳实践

```python
# ✅ 好：参数化查询（防 SQL 注入）
stmt = select(User).where(User.email == email)

# ❌ 坏：⚠️ 禁止裸 SQL 拼接
text(f"SELECT * FROM users WHERE email = '{email}'")   # ← SQL 注入风险

# ✅ 好：批量更新
stmt = update(User).where(User.is_active == False).values(status="inactive")
await db.execute(stmt)
await db.commit()
```
