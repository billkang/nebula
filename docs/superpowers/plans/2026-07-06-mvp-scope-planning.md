# Nebula MVP v1 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 搭建 Nebula AI Agent 中台平台 v1——一个 Web 应用，PM 通过对话澄清需求，借助 OpenSpec 生成结构化设计文档，调用本地 Claude Code 执行编码，产出版本化的 Build Artifact。

**架构：** React + Vite 前端通过 REST API 与 FastAPI 后端通信。LangGraph StateGraph 驱动五阶段需求澄清对话流。OpenSpec CLI 负责文档生成。本地 Claude Code 通过 subprocess 执行编码。数据库 v1 用 SQLite，可配置切换 PostgreSQL。

**技术栈：** Python/FastAPI, React/Vite/TypeScript/Tailwind, LangGraph, SQLAlchemy/Alembic, JWT (python-jose), OpenSpec CLI, Claude Code CLI

## 全局约束

- Python 3.11+, Node.js 18+ 必须
- PEP 8 风格、type hints 必须、ruff 格式化
- React 仅函数组件 + hooks
- Commit 用中文，代码标识符用英文
- SQLite v1（不用 PostgreSQL 特有 SQL）
- JWT 24h 有效期
- 两级角色：admin（全权限）、member（使用平台）
- 内置用户：admin/123456, pm/123456
- 所有 specs 使用 WHEN/THEN 场景格式

---

## 文件结构

```
nebula/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # FastAPI 应用入口 + CORS
│   │   ├── config.py                  # pydantic-settings (.env)
│   │   ├── database.py                # SQLAlchemy engine + session
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── user.py                # User 模型
│   │   │   ├── project.py             # Project 模型
│   │   │   ├── session.py             # Session 模型
│   │   │   └── message.py             # Message 模型
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py                # 认证请求/响应 schema
│   │   │   ├── project.py             # 项目 schema
│   │   │   ├── chat.py                # 对话 schema
│   │   │   ├── doc.py                 # 文档 schema
│   │   │   ├── executor.py            # 执行器 schema
│   │   │   └── build.py               # 构建 schema
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── router.py              # 全局路由聚合
│   │   │   ├── auth.py                # 认证路由
│   │   │   ├── projects.py            # 项目路由
│   │   │   ├── chat.py                # 对话路由
│   │   │   ├── documents.py           # 文档路由
│   │   │   ├── executor.py            # 执行器路由
│   │   │   └── build.py               # 构建路由
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── auth_service.py        # 认证业务逻辑
│   │   │   ├── project_service.py     # 项目业务逻辑
│   │   │   ├── chat_service.py        # 对话 + Agent 编排
│   │   │   ├── doc_service.py         # OpenSpec 集成
│   │   │   ├── executor_service.py    # Claude Code 执行
│   │   │   └── build_service.py       # 构建验证 + 打包
│   │   ├── agent/
│   │   │   ├── __init__.py
│   │   │   ├── state.py               # ChatState TypedDict
│   │   │   ├── nodes.py               # 阶段 node 函数
│   │   │   └── graph.py              # StateGraph 定义
│   │   └── middleware/
│   │       ├── __init__.py
│   │       └── auth.py                # JWT 依赖注入
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py                # 测试夹具
│   │   ├── test_auth.py
│   │   ├── test_projects.py
│   │   ├── test_chat.py
│   │   └── test_build.py
│   ├── alembic/
│   │   └── ...                        # alembic init 自动生成
│   ├── alembic.ini
│   ├── seed.py                        # 初始用户种子脚本
│   ├── requirements.txt
│   └── .env.example
├── frontend/
│   ├── src/
│   │   ├── main.tsx                   # React 入口
│   │   ├── App.tsx                    # 路由配置
│   │   ├── api/
│   │   │   └── client.ts             # API 客户端（fetch 封装）
│   │   ├── store/
│   │   │   └── index.ts              # zustand store
│   │   ├── pages/
│   │   │   ├── Login.tsx
│   │   │   ├── Register.tsx
│   │   │   ├── Projects.tsx
│   │   │   ├── Chat.tsx
│   │   │   └── Docs.tsx
│   │   ├── components/
│   │   │   ├── AppLayout.tsx
│   │   │   ├── Sidebar.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── MessageInput.tsx
│   │   │   ├── ConfirmCard.tsx
│   │   │   ├── DocViewer.tsx
│   │   │   └── StatusBadge.tsx
│   │   └── index.css                  # Tailwind 导入
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   ├── vite.config.ts
│   └── tailwind.config.js
├── projects/                          # 生成的项目代码输出
├── openspec/
│   └── changes/
│       └── mvp-scope-planning/        # 当前 change SDD
├── docker-compose.yml                 # v1 占位
├── .env
├── .env.example
└── README.md
```

---

## 实现任务

### Task 1：后端基础框架

**文件：**
- 新建：`backend/requirements.txt`
- 新建：`backend/.env.example`
- 新建：`backend/app/__init__.py`
- 新建：`backend/app/main.py`
- 新建：`backend/app/config.py`
- 新建：`backend/app/database.py`
- 新建：`backend/alembic.ini`（通过 alembic init）

**接口：**
- 消费：无（基础任务）
- 产出：`app.main:app` FastAPI 实例、Config 类（DB URL / JWT secret / CORS origins）、Database session factory

- [ ] **Step 1：创建 requirements.txt**

```txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.35
alembic==1.13.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==2.9.0
pydantic-settings==2.5.0
python-multipart==0.0.9
langgraph==0.2.0
langchain-openai==0.2.0
httpx==0.27.0
pytest==8.3.0
```

- [ ] **Step 2：创建 .env.example**

```txt
DATABASE_URL=sqlite:///./nebula.db
JWT_SECRET=change-me-to-a-random-secret
JWT_EXPIRY_HOURS=24
CORS_ORIGINS=http://localhost:5173
ADMIN_USERNAME=admin
ADMIN_PASSWORD=123456
PM_USERNAME=pm
PM_PASSWORD=123456
```

- [ ] **Step 3：创建 config.py**

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    database_url: str = "sqlite:///./nebula.db"
    jwt_secret: str = "change-me-to-a-random-secret"
    jwt_expiry_hours: int = 24
    cors_origins: str = "http://localhost:5173"
    admin_username: str = "admin"
    admin_password: str = "123456"
    pm_username: str = "pm"
    pm_password: str = "123456"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}

settings = Settings()
```

- [ ] **Step 4：创建 database.py**

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.config import settings

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {},
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 5：创建 main.py**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database import engine, Base
from app.api.router import api_router

app = FastAPI(title="Nebula API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

app.include_router(api_router, prefix="/api/v1")
```

- [ ] **Step 6：创建 api/router.py**

```python
from fastapi import APIRouter

api_router = APIRouter()
# 后续 task 注册路由：
# api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
```

- [ ] **Step 7：初始化 Alembic**

```bash
cd backend && alembic init alembic
```

编辑 `alembic.ini`，设置 `sqlalchemy.url = sqlite:///./nebula.db`

- [ ] **Step 8：创建空的 `__init__.py`**

```python
# backend/app/__init__.py — 空
# backend/app/models/__init__.py — 后续引入 models
```

- [ ] **Step 9：验证基础框架**

```bash
cd backend && pip install -r requirements.txt && python -c "from app.main import app; print('OK')"
```

预期输出：`OK`

---

### Task 2：用户认证 — 后端模型 + Schema

**文件：**
- 新建：`backend/app/models/__init__.py`
- 新建：`backend/app/models/user.py`
- 新建：`backend/app/schemas/__init__.py`
- 新建：`backend/app/schemas/auth.py`
- 新建：`backend/app/middleware/__init__.py`
- 新建：`backend/app/middleware/auth.py`

**接口：**
- 消费：`Base`（来自 `app.database`）、`settings`（来自 `app.config`）
- 产出：`User` 模型、`Token`/`LoginRequest`/`RegisterRequest`/`UserResponse` schema、`get_current_user` 依赖注入

- [ ] **Step 1：创建 models/user.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SAEnum
from sqlalchemy.dialects.sqlite import TEXT
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    MEMBER = "member"

class User(Base):
    __tablename__ = "users"

    id = Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.MEMBER, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2：创建 schemas/auth.py**

```python
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    username: str = Field(min_length=2, max_length=50)
    email: EmailStr
    password: str = Field(min_length=6)

class LoginRequest(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str
    created_at: str
```

- [ ] **Step 3：创建 middleware/auth.py**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError, jwt
from sqlalchemy.orm import Session
from app.config import settings
from app.database import get_db
from app.models.user import User

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_admin(user: User = Depends(get_current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
```

- [ ] **Step 4：更新 models/__init__.py**

```python
from app.models.user import User, UserRole
```

- [ ] **Step 5：更新 schemas/__init__.py**

```python
from app.schemas.auth import RegisterRequest, LoginRequest, Token, UserResponse
```

---

### Task 3：用户认证 — 后端 API

**文件：**
- 新建：`backend/app/services/__init__.py`
- 新建：`backend/app/services/auth_service.py`
- 新建：`backend/app/api/auth.py`
- 修改：`backend/app/api/router.py`（注册认证路由）

**接口：**
- 消费：`User` 模型、`RegisterRequest`/`LoginRequest` schema、`get_current_user` 依赖注入
- 产出：`POST /api/v1/auth/register`、`POST /api/v1/auth/login`、`GET /api/v1/auth/me`

- [ ] **Step 1：创建 services/auth_service.py**

```python
from datetime import datetime, timedelta, timezone
from jose import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.config import settings
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, UserResponse

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expiry_hours)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm="HS256")

def register(req: RegisterRequest, db: Session) -> UserResponse:
    if db.query(User).filter(User.email == req.email).first():
        raise HTTPException(status_code=400, detail="该邮箱已被注册")
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(status_code=400, detail="该用户名已被使用")
    user = User(
        username=req.username,
        email=req.email,
        password=hash_password(req.password),
        role=UserRole.MEMBER,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        created_at=user.created_at.isoformat(),
    )

def login(req: LoginRequest, db: Session) -> tuple[str, UserResponse]:
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not verify_password(req.password, user.password):
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    token = create_token(user.id)
    return token, UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        created_at=user.created_at.isoformat(),
    )
```

- [ ] **Step 2：创建 api/auth.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, Token, UserResponse
from app.services.auth_service import register, login
from app.middleware.auth import get_current_user
from app.models.user import User

auth_router = APIRouter(prefix="/auth", tags=["auth"])

@auth_router.post("/register", response_model=UserResponse)
def register_user(req: RegisterRequest, db: Session = Depends(get_db)):
    return register(req, db)

@auth_router.post("/login", response_model=Token)
def login_user(req: LoginRequest, db: Session = Depends(get_db)):
    token, user = login(req, db)
    return Token(access_token=token, user=user)

@auth_router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)):
    return UserResponse(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role.value,
        created_at=user.created_at.isoformat(),
    )
```

- [ ] **Step 3：更新 api/router.py**

```python
from fastapi import APIRouter
from app.api.auth import auth_router

api_router = APIRouter()
api_router.include_router(auth_router)
```

---

### Task 4：用户认证 — 种子脚本 + 测试

**文件：**
- 新建：`backend/seed.py`
- 新建：`backend/tests/__init__.py`
- 新建：`backend/tests/conftest.py`
- 新建：`backend/tests/test_auth.py`

- [ ] **Step 1：创建 seed.py**

```python
from app.database import SessionLocal, engine, Base
from app.models.user import User, UserRole
from app.services.auth_service import hash_password
from app.config import settings

def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if not db.query(User).filter(User.username == settings.admin_username).first():
            admin = User(
                username=settings.admin_username,
                email="admin@nebula.local",
                password=hash_password(settings.admin_password),
                role=UserRole.ADMIN,
            )
            db.add(admin)
            print(f"创建 admin 用户: {settings.admin_username}")
        if not db.query(User).filter(User.username == settings.pm_username).first():
            pm = User(
                username=settings.pm_username,
                email="pm@nebula.local",
                password=hash_password(settings.pm_password),
                role=UserRole.MEMBER,
            )
            db.add(pm)
            print(f"创建 pm 用户: {settings.pm_username}")
        db.commit()
    finally:
        db.close()

if __name__ == "__main__":
    seed()
```

- [ ] **Step 2：创建 tests/conftest.py**

```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base, get_db
from app.main import app
from app.models.user import User, UserRole
from app.services.auth_service import hash_password

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
```

- [ ] **Step 3：创建 tests/test_auth.py**

```python
from app.models.user import User, UserRole
from app.services.auth_service import hash_password, verify_password

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
    db.add(user); db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "loginuser", "password": "pass123"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_login_wrong_password(client, db):
    user = User(username="loginfail", email="fail@test.com",
                password=hash_password("correct"), role=UserRole.MEMBER)
    db.add(user); db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "loginfail", "password": "wrong"})
    assert resp.status_code == 401
```

- [ ] **Step 4：运行测试，确认通过**

```bash
cd backend && python -m pytest tests/test_auth.py -v
```

预期输出：5 passed

---

### Task 5：项目管理 — 后端

**文件：**
- 新建：`backend/app/models/project.py`
- 新建：`backend/app/schemas/project.py`
- 新建：`backend/app/services/project_service.py`
- 新建：`backend/app/api/projects.py`
- 新建：`backend/tests/test_projects.py`
- 修改：`backend/app/api/router.py`（注册项目路由）
- 修改：`backend/app/models/__init__.py`

- [ ] **Step 1：创建 models/project.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import TEXT
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(200), nullable=False)
    description = Column(String(1000), default="")
    owner_id = Column(TEXT, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2：创建 schemas/project.py**

```python
from pydantic import BaseModel, Field

class ProjectCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=1000)

class ProjectResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
```

- [ ] **Step 3：创建 services/project_service.py**

```python
from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse

class ProjectService:
    @staticmethod
    def list_projects(db: Session, user: User) -> list[ProjectResponse]:
        projects = db.query(Project).filter(Project.owner_id == user.id
            ).order_by(Project.created_at.desc()).all()
        return [ProjectResponse(
            id=p.id, name=p.name, description=p.description,
            created_at=p.created_at.isoformat(), updated_at=p.updated_at.isoformat(),
        ) for p in projects]

    @staticmethod
    def create_project(req: ProjectCreate, db: Session, user: User) -> ProjectResponse:
        project = Project(name=req.name, description=req.description, owner_id=user.id)
        db.add(project); db.commit(); db.refresh(project)
        return ProjectResponse(
            id=project.id, name=project.name, description=project.description,
            created_at=project.created_at.isoformat(), updated_at=project.updated_at.isoformat(),
        )

    @staticmethod
    def get_project(project_id: str, db: Session, user: User) -> ProjectResponse:
        project = db.query(Project).filter(
            Project.id == project_id, Project.owner_id == user.id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        return ProjectResponse(
            id=project.id, name=project.name, description=project.description,
            created_at=project.created_at.isoformat(), updated_at=project.updated_at.isoformat(),
        )

    @staticmethod
    def delete_project(project_id: str, db: Session, user: User):
        project = db.query(Project).filter(
            Project.id == project_id, Project.owner_id == user.id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        db.delete(project); db.commit()
```

- [ ] **Step 4：创建 api/projects.py**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse
from app.services.project_service import ProjectService

projects_router = APIRouter(prefix="/projects", tags=["projects"])

@projects_router.get("", response_model=list[ProjectResponse])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return ProjectService.list_projects(db, user)

@projects_router.post("", response_model=ProjectResponse)
def create_project(req: ProjectCreate, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    return ProjectService.create_project(req, db, user)

@projects_router.get("/{project_id}", response_model=ProjectResponse)
def get_project(project_id: str, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    return ProjectService.get_project(project_id, db, user)

@projects_router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    ProjectService.delete_project(project_id, db, user)
    return {"message": "项目已删除"}
```

- [ ] **Step 5：更新 api/router.py**

```python
from fastapi import APIRouter
from app.api.auth import auth_router
from app.api.projects import projects_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
```

- [ ] **Step 6：更新 models/__init__.py**

```python
from app.models.user import User, UserRole
from app.models.project import Project
```

- [ ] **Step 7：创建 tests/test_projects.py**

```python
def test_create_project(client, db):
    # 先创建用户并获取 token
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="projuser", email="proj@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user); db.commit()
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
    db.add(user); db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "listuser", "password": "pass123"})
    token = resp.json()["access_token"]

    resp = client.get("/api/v1/projects", headers={"Authorization": f"Bearer {token}"})
    assert resp.json() == []

def test_delete_project(client, db):
    from app.models.user import User, UserRole
    from app.services.auth_service import hash_password
    user = User(username="deluser", email="del@test.com",
                password=hash_password("pass123"), role=UserRole.ADMIN)
    db.add(user); db.commit()
    resp = client.post("/api/v1/auth/login", json={"username": "deluser", "password": "pass123"})
    token = resp.json()["access_token"]

    create = client.post("/api/v1/projects", json={"name": "待删除"},
                         headers={"Authorization": f"Bearer {token}"})
    pid = create.json()["id"]
    resp = client.delete(f"/api/v1/projects/{pid}",
                         headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200
```

---

### Task 6：对话 Agent — 后端模型 + StateGraph

**文件：**
- 新建：`backend/app/models/session.py`
- 新建：`backend/app/models/message.py`
- 新建：`backend/app/agent/__init__.py`
- 新建：`backend/app/agent/state.py`
- 新建：`backend/app/agent/nodes.py`
- 新建：`backend/app/agent/graph.py`
- 修改：`backend/app/models/__init__.py`

- [ ] **Step 1：创建 models/session.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.dialects.sqlite import TEXT
from app.database import Base

class Session(Base):
    __tablename__ = "sessions"

    id = Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(TEXT, ForeignKey("projects.id"), nullable=False)
    status = Column(String(20), default="active")  # active | completed
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc),
                         onupdate=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 2：创建 models/message.py**

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.sqlite import TEXT
from app.database import Base

class Message(Base):
    __tablename__ = "messages"

    id = Column(TEXT, primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(TEXT, ForeignKey("sessions.id"), nullable=False)
    role = Column(String(10), nullable=False)  # user | agent
    content = Column(Text, nullable=False)
    phase = Column(String(20), nullable=True)  # greeting | collecting | clarifying | confirming | generating
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
```

- [ ] **Step 3：创建 agent/state.py**

```python
from typing import TypedDict, Optional, Annotated
from langgraph.graph.message import add_messages

class ChatState(TypedDict):
    messages: Annotated[list, add_messages]
    phase: str  # greeting | collecting | clarifying | confirming | generating
    req_summary: Optional[str]
    out_of_scope: Optional[list[str]]
    project_id: Optional[str]
    session_id: Optional[str]
```

- [ ] **Step 4：创建 agent/nodes.py**

```python
from typing import Any
from app.agent.state import ChatState

def greeting_node(state: ChatState) -> dict:
    """问候阶段 — 欢迎用户并引导描述需求"""
    return {
        "messages": [{"role": "assistant", "content": "欢迎来到星云！请描述你的需求——你可以提新功能、改动现有功能，或者上传 PRD。"}],
        "phase": "greeting",
    }

def collect_node(state: ChatState) -> dict:
    """收集需求阶段 — 追问核心信息"""
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    if len(last_user_msg) > 50:
        summary = f"用户需求：{last_user_msg[:200]}"
        return {"phase": "clarifying", "req_summary": summary}

    return {
        "messages": [{"role": "assistant", "content": "能具体说说你想实现什么目标吗？涉及哪些功能模块？"}],
    }

def clarify_node(state: ChatState) -> dict:
    """澄清细节阶段 — 追问模糊点"""
    last_user_msg = ""
    for msg in reversed(state["messages"]):
        if msg.get("role") == "user":
            last_user_msg = msg.get("content", "")
            break

    current_summary = state.get("req_summary", "")
    if last_user_msg and len(last_user_msg) > 10:
        current_summary += f"\n补充：{last_user_msg[:200]}"

    user_msg_count = sum(1 for m in state["messages"] if m.get("role") == "user")
    if user_msg_count >= 3:
        return {"phase": "confirming", "req_summary": current_summary}

    return {
        "messages": [{"role": "assistant", "content": "了解了。有没有什么技术约束或偏好？比如技术栈、部署方式、性能要求？\n\n另外，**第一版明确不做什么？** 有什么是你可以接受推迟的？"}],
        "req_summary": current_summary,
    }

def confirm_node(state: ChatState) -> dict:
    """确认范围阶段 — 展示摘要请求确认"""
    summary = state.get("req_summary", "")
    scope_list = state.get("out_of_scope", [])

    content = f"""我已经整理了你的需求，请确认以下范围是否准确：

## ✅ 需求摘要
{summary}

## ❌ 不做（Out of Scope）
"""
    if scope_list:
        for item in scope_list:
            content += f"- {item}\n"
    else:
        content += "- （暂未列出，你可补充）\n"

    content += "\n以上范围正确吗？你可以：\n- ✅ **确认** — 范围正确，开始生成设计文档\n- ✏️ **补充** — 我需要调整或补充内容"

    return {"messages": [{"role": "assistant", "content": content}]}

def generate_node(state: ChatState) -> dict:
    """生成文档阶段 — 通知用户可触发文档生成"""
    return {
        "messages": [{"role": "assistant", "content": "好的，已明确需求范围！请点击下方的「生成设计文档」按钮，我将为你生成完整的设计文档。"}],
        "phase": "generating",
    }
```

- [ ] **Step 5：创建 agent/graph.py**

```python
from langgraph.graph import StateGraph, START, END
from app.agent.state import ChatState
from app.agent.nodes import greeting_node, collect_node, clarify_node, confirm_node, generate_node

def router(state: ChatState) -> str:
    """根据最后一条消息决定流转方向"""
    last_msg = state["messages"][-1] if state["messages"] else {}
    content = last_msg.get("content", "") if isinstance(last_msg, dict) else ""

    if state["phase"] == "greeting":
        return "collect"
    elif state["phase"] == "collecting":
        return "clarify"
    elif state["phase"] == "clarifying":
        return "confirm"
    elif state["phase"] == "confirming":
        confirm_keywords = ["确认", "正确", "没问题", "可以", "是的", "对", "ok", "yes", "confirm", "✅"]
        revise_keywords = ["修改", "调整", "补充", "不对", "不是", "遗漏", "加上", "添加", "少"]
        if any(kw in content.lower() for kw in confirm_keywords):
            return "generate"
        elif any(kw in content.lower() for kw in revise_keywords):
            return "collect"
        return "confirm"
    elif state["phase"] == "generating":
        return END
    return END

def build_agent() -> StateGraph:
    graph = StateGraph(ChatState)

    graph.add_node("greeting", greeting_node)
    graph.add_node("collect", collect_node)
    graph.add_node("clarify", clarify_node)
    graph.add_node("confirm", confirm_node)
    graph.add_node("generate", generate_node)

    graph.add_conditional_edges("greeting", router, {"collect": "collect"})
    graph.add_conditional_edges("collect", router, {"clarify": "clarify"})
    graph.add_conditional_edges("clarify", router, {"confirm": "confirm"})
    graph.add_conditional_edges("confirm", router, {
        "generate": "generate", "collect": "collect", "confirm": "confirm",
    })

    graph.add_edge(START, "greeting")
    graph.add_edge("generate", END)

    return graph.compile()

agent = build_agent()
```

- [ ] **Step 6：更新 models/__init__.py**

```python
from app.models.user import User, UserRole
from app.models.project import Project
from app.models.session import Session
from app.models.message import Message
```

- [ ] **Step 7：验证 LangGraph 编译**

```bash
cd backend && python -c "from app.agent.graph import agent; print('LangGraph agent compiled successfully')"
```

预期输出：`LangGraph agent compiled successfully`

---

### Task 7：对话 Agent — 后端 API

**文件：**
- 新建：`backend/app/schemas/chat.py`
- 新建：`backend/app/services/chat_service.py`
- 新建：`backend/app/api/chat.py`

- [ ] **Step 1：创建 schemas/chat.py**

```python
from pydantic import BaseModel
from typing import Optional

class MessageSend(BaseModel):
    content: str

class MessageResponse(BaseModel):
    id: str
    role: str
    content: str
    phase: Optional[str] = None
    created_at: str

class SessionResponse(BaseModel):
    id: str
    project_id: str
    status: str
    created_at: str
```

- [ ] **Step 2：创建 services/chat_service.py**

```python
from sqlalchemy.orm import Session as DBSession
from app.models.session import Session
from app.models.message import Message
from app.models.user import User
from app.schemas.chat import MessageResponse, SessionResponse
from app.agent.graph import agent
from app.agent.state import ChatState

# 每个 session 对应一个 Agent 内存状态
agent_states: dict[str, ChatState] = {}

class ChatService:
    @staticmethod
    def create_session(project_id: str, db: DBSession) -> SessionResponse:
        session = Session(project_id=project_id)
        db.add(session); db.commit(); db.refresh(session)

        agent_states[session.id] = {
            "messages": [], "phase": "greeting",
            "req_summary": None, "out_of_scope": None,
            "project_id": project_id, "session_id": session.id,
        }
        return SessionResponse(
            id=session.id, project_id=session.project_id,
            status=session.status, created_at=session.created_at.isoformat(),
        )

    @staticmethod
    def get_sessions(project_id: str, db: DBSession) -> list[SessionResponse]:
        sessions = db.query(Session).filter(Session.project_id == project_id
            ).order_by(Session.created_at.desc()).all()
        return [SessionResponse(
            id=s.id, project_id=s.project_id, status=s.status,
            created_at=s.created_at.isoformat(),
        ) for s in sessions]

    @staticmethod
    def get_messages(session_id: str, db: DBSession) -> list[MessageResponse]:
        messages = db.query(Message).filter(Message.session_id == session_id
            ).order_by(Message.created_at.asc()).all()
        return [MessageResponse(
            id=m.id, role=m.role, content=m.content, phase=m.phase,
            created_at=m.created_at.isoformat(),
        ) for m in messages]

    @staticmethod
    def send_message(session_id: str, content: str, user: User,
                     db: DBSession) -> list[MessageResponse]:
        # 保存用户消息
        user_msg = Message(session_id=session_id, role="user", content=content)
        db.add(user_msg); db.commit(); db.refresh(user_msg)

        # 获取/初始化 Agent 状态
        if session_id not in agent_states:
            session = db.query(Session).filter(Session.id == session_id).first()
            if not session:
                raise ValueError("Session not found")
            agent_states[session_id] = {
                "messages": [], "phase": "greeting",
                "req_summary": None, "out_of_scope": None,
                "project_id": session.project_id, "session_id": session_id,
            }

        state = agent_states[session_id]
        state["messages"].append({"role": "user", "content": content})

        # 运行 Agent
        result = agent.invoke(state)

        # 提取 Agent 响应
        agent_msg_content = ""
        for msg in reversed(result["messages"]):
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                agent_msg_content = msg.get("content", "")
                break

        # 保存 Agent 消息
        agent_msg = Message(
            session_id=session_id, role="agent",
            content=agent_msg_content, phase=result.get("phase"),
        )
        db.add(agent_msg); db.commit(); db.refresh(agent_msg)

        # 更新内存状态
        agent_states[session_id] = result

        return ChatService.get_messages(session_id, db)
```

- [ ] **Step 3：创建 api/chat.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.schemas.chat import MessageSend, MessageResponse, SessionResponse
from app.services.chat_service import ChatService

chat_router = APIRouter(prefix="/projects/{project_id}/sessions", tags=["chat"])

@chat_router.get("", response_model=list[SessionResponse])
def list_sessions(project_id: str, db: DBSession = Depends(get_db),
                  user: User = Depends(get_current_user)):
    return ChatService.get_sessions(project_id, db)

@chat_router.post("", response_model=SessionResponse)
def create_session(project_id: str, db: DBSession = Depends(get_db),
                   user: User = Depends(get_current_user)):
    return ChatService.create_session(project_id, db)

@chat_router.get("/{session_id}/messages", response_model=list[MessageResponse])
def get_messages(session_id: str, db: DBSession = Depends(get_db),
                 user: User = Depends(get_current_user)):
    return ChatService.get_messages(session_id, db)

@chat_router.post("/{session_id}/messages", response_model=list[MessageResponse])
def send_message(session_id: str, req: MessageSend, db: DBSession = Depends(get_db),
                 user: User = Depends(get_current_user)):
    try:
        return ChatService.send_message(session_id, req.content, user, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
```

- [ ] **Step 4：更新 api/router.py**

```python
from fastapi import APIRouter
from app.api.auth import auth_router
from app.api.projects import projects_router
from app.api.chat import chat_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(chat_router)
```

---

### Task 8：文档生成 — 后端

**文件：**
- 新建：`backend/app/schemas/doc.py`
- 新建：`backend/app/services/doc_service.py`
- 新建：`backend/app/api/documents.py`
- 修改：`backend/app/api/router.py`

- [ ] **Step 1：创建 schemas/doc.py**

```python
from pydantic import BaseModel
from typing import Optional

class DocGenerateRequest(BaseModel):
    req_summary: Optional[str] = None
    out_of_scope: Optional[list[str]] = None

class DocInfo(BaseModel):
    type: str  # proposal | specs | design | tasks
    path: str
    exists: bool

class DocGenerateResponse(BaseModel):
    success: bool
    message: str
    docs: list[DocInfo]
```

- [ ] **Step 2：创建 services/doc_service.py**

```python
import subprocess
import os
from pathlib import Path

CHANGE_NAME = "mvp-scope-planning"
CHANGE_DIR = f"openspec/changes/{CHANGE_NAME}"
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class DocService:
    @staticmethod
    def get_change_dir() -> str:
        return str(BASE_DIR.parent / CHANGE_DIR)

    @staticmethod
    def generate_docs(req_summary: str | None = None,
                      out_of_scope: list[str] | None = None) -> dict:
        change_dir = DocService.get_change_dir()

        for cmd in ["proposal", "specs", "design", "tasks"]:
            result = subprocess.run(
                ["openspec", "instructions", cmd, "--change", CHANGE_NAME, "--json"],
                capture_output=True, text=True, cwd=BASE_DIR.parent,
            )
            if result.returncode != 0:
                return {"success": False,
                        "message": f"{cmd} 生成失败: {result.stderr}"}

        return {"success": True, "message": "文档生成完成"}

    @staticmethod
    def list_docs() -> list[dict]:
        change_dir = DocService.get_change_dir()
        docs = [
            {"type": "proposal", "path": os.path.join(change_dir, "proposal.md"),
             "exists": os.path.exists(os.path.join(change_dir, "proposal.md"))},
            {"type": "specs", "path": os.path.join(change_dir, "specs"),
             "exists": os.path.isdir(os.path.join(change_dir, "specs"))},
            {"type": "design", "path": os.path.join(change_dir, "design.md"),
             "exists": os.path.exists(os.path.join(change_dir, "design.md"))},
            {"type": "tasks", "path": os.path.join(change_dir, "tasks.md"),
             "exists": os.path.exists(os.path.join(change_dir, "tasks.md"))},
        ]
        return docs

    @staticmethod
    def get_doc(doc_type: str) -> str | None:
        change_dir = DocService.get_change_dir()
        path_map = {
            "proposal": "proposal.md",
            "design": "design.md",
            "tasks": "tasks.md",
        }
        if doc_type in path_map:
            path = os.path.join(change_dir, path_map[doc_type])
            if os.path.isfile(path):
                with open(path) as f:
                    return f.read()
        elif doc_type == "specs":
            specs_dir = os.path.join(change_dir, "specs")
            if os.path.isdir(specs_dir):
                content = ""
                for root, _, fnames in os.walk(specs_dir):
                    for fname in sorted(fnames):
                        if fname.endswith(".md"):
                            filepath = os.path.join(root, fname)
                            with open(filepath) as f:
                                content += f"## {os.path.relpath(filepath, specs_dir)}\n\n{f.read()}\n\n"
                return content
        return None
```

- [ ] **Step 3：创建 api/documents.py**

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.doc_service import DocService

doc_router = APIRouter(prefix="/projects/{project_id}/docs", tags=["documents"])

@doc_router.get("")
def list_docs(project_id: str, db: Session = Depends(get_db),
              user: User = Depends(get_current_user)):
    return DocService.list_docs()

@doc_router.get("/{doc_type}")
def get_doc(project_id: str, doc_type: str, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    content = DocService.get_doc(doc_type)
    if content is None:
        raise HTTPException(status_code=404, detail="文档不存在")
    return {"type": doc_type, "content": content}

@doc_router.post("/generate")
def generate_docs(project_id: str, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    return DocService.generate_docs()
```

- [ ] **Step 4：更新 api/router.py**

```python
from fastapi import APIRouter
from app.api.auth import auth_router
from app.api.projects import projects_router
from app.api.chat import chat_router
from app.api.documents import doc_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(doc_router)
api_router.include_router(chat_router)
```

---

### Task 9：执行器 + 构建 — 后端

**文件：**
- 新建：`backend/app/schemas/executor.py`
- 新建：`backend/app/schemas/build.py`
- 新建：`backend/app/services/executor_service.py`
- 新建：`backend/app/services/build_service.py`
- 新建：`backend/app/api/executor.py`
- 新建：`backend/app/api/build.py`
- 修改：`backend/app/api/router.py`

- [ ] **Step 1：创建 schemas/executor.py**

```python
from pydantic import BaseModel
from typing import Optional

class ExecuteStatus(BaseModel):
    status: str  # idle | running | success | failed
    message: Optional[str] = None
```

- [ ] **Step 2：创建 schemas/build.py**

```python
from pydantic import BaseModel
from typing import Optional

class BuildStatus(BaseModel):
    status: str  # idle | testing | verifying | packaging | success | failed
    message: Optional[str] = None

class ArtifactInfo(BaseModel):
    version: str
    created_at: str
    path: str
```

- [ ] **Step 3：创建 services/executor_service.py**

```python
import subprocess
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class ExecutorService:
    status: str = "idle"
    message: str | None = None

    @staticmethod
    def check_prerequisites() -> tuple[bool, str]:
        """检查 Claude Code 是否可用"""
        try:
            result = subprocess.run(["claude", "--version"],
                                    capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True, result.stdout.strip()
            return False, "Claude Code CLI 无响应"
        except FileNotFoundError:
            return False, "未找到 Claude Code CLI，请安装：npm install -g @anthropic-ai/claude-code"
        except subprocess.TimeoutExpired:
            return False, "Claude Code 检查超时"

    @staticmethod
    def get_status() -> dict:
        return {"status": ExecutorService.status, "message": ExecutorService.message}

    @staticmethod
    def execute(project_id: str) -> dict:
        available, msg = ExecutorService.check_prerequisites()
        if not available:
            ExecutorService.status = "failed"
            ExecutorService.message = msg
            return ExecutorService.get_status()

        project_dir = BASE_DIR.parent / "projects" / project_id / "src"
        project_dir.mkdir(parents=True, exist_ok=True)

        ExecutorService.status = "running"
        ExecutorService.message = "编码执行中..."

        instruction = "请根据 specs 和 tasks 实现功能代码。"

        try:
            result = subprocess.run(
                ["claude", "code", "--prompt", instruction],
                capture_output=True, text=True,
                cwd=str(project_dir), timeout=3600,
            )
            if result.returncode == 0:
                ExecutorService.status = "success"
                ExecutorService.message = "编码执行完成"
            else:
                ExecutorService.status = "failed"
                ExecutorService.message = f"编码执行失败: {result.stderr[:500]}"
        except subprocess.TimeoutExpired:
            ExecutorService.status = "failed"
            ExecutorService.message = "编码执行超时（超过1小时）"

        return ExecutorService.get_status()
```

- [ ] **Step 4：创建 services/build_service.py**

```python
import subprocess, json, os, tarfile
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

class BuildService:
    status: str = "idle"
    message: str = ""

    @staticmethod
    def run_tests(project_dir: Path) -> tuple[bool, str]:
        result = subprocess.run(
            ["python", "-m", "pytest", "--tb=short", "-q"],
            capture_output=True, text=True, cwd=str(project_dir), timeout=300,
        )
        return result.returncode == 0, result.stdout + result.stderr

    @staticmethod
    def verify_integrity(project_dir: Path) -> list[str]:
        missing = []
        for item in ["src", "requirements.txt", "Dockerfile"]:
            if not (project_dir / item).exists():
                missing.append(item)
        return missing

    @staticmethod
    def package_artifact(project_dir: Path, version: str) -> tuple[str, dict]:
        artifact_dir = project_dir.parent / "artifacts" / version
        artifact_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entry": "src/main.py",
            "dependencies": [],
        }
        req_file = project_dir / "requirements.txt"
        if req_file.exists():
            with open(req_file) as f:
                manifest["dependencies"] = [
                    line.strip() for line in f
                    if line.strip() and not line.startswith("#")
                ]

        manifest_path = artifact_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        tar_path = artifact_dir / "artifact.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(project_dir / "src", arcname="src")
            tar.add(project_dir / "requirements.txt", arcname="requirements.txt")
            tar.add(project_dir / "Dockerfile", arcname="Dockerfile")
            tar.add(manifest_path, arcname="manifest.json")

        return str(tar_path), manifest

    @staticmethod
    def build(project_id: str) -> dict:
        project_dir = BASE_DIR.parent / "projects" / project_id

        BuildService.status = "testing"
        BuildService.message = "正在运行测试..."
        passed, output = BuildService.run_tests(project_dir)
        if not passed:
            BuildService.status = "failed"
            BuildService.message = f"测试失败:\n{output[:500]}"
            return BuildService.get_status()

        BuildService.status = "verifying"
        BuildService.message = "正在验证完整性..."
        missing = BuildService.verify_integrity(project_dir)
        if missing:
            BuildService.status = "failed"
            BuildService.message = f"缺少必要文件: {', '.join(missing)}"
            return BuildService.get_status()

        BuildService.status = "packaging"
        BuildService.message = "正在打包 Artifact..."
        tar_path, manifest = BuildService.package_artifact(project_dir, "v1")

        BuildService.status = "success"
        BuildService.message = f"构建完成，Artifact: {tar_path}"
        return BuildService.get_status()

    @staticmethod
    def get_status() -> dict:
        return {"status": BuildService.status, "message": BuildService.message}

    @staticmethod
    def list_artifacts(project_id: str) -> list[dict]:
        artifacts_dir = BASE_DIR.parent / "projects" / project_id / "artifacts"
        if not artifacts_dir.exists():
            return []
        artifacts = []
        for version_dir in sorted(artifacts_dir.iterdir()):
            if version_dir.is_dir():
                mf = version_dir / "manifest.json"
                if mf.exists():
                    with open(mf) as f:
                        m = json.load(f)
                    artifacts.append({
                        "version": version_dir.name,
                        "created_at": m.get("created_at", ""),
                        "path": str(version_dir),
                    })
        return artifacts
```

- [ ] **Step 5：创建 api/executor.py**

```python
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.executor_service import ExecutorService

executor_router = APIRouter(prefix="/projects/{project_id}/execute", tags=["executor"])

@executor_router.post("")
def execute(project_id: str, user: User = Depends(get_current_user)):
    return ExecutorService.execute(project_id)

@executor_router.get("/status")
def execute_status(project_id: str, user: User = Depends(get_current_user)):
    return ExecutorService.get_status()
```

- [ ] **Step 6：创建 api/build.py**

```python
from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.build_service import BuildService

build_router = APIRouter(prefix="/projects/{project_id}/build", tags=["build"])

@build_router.post("")
def trigger_build(project_id: str, user: User = Depends(get_current_user)):
    return BuildService.build(project_id)

@build_router.get("/status")
def build_status(project_id: str, user: User = Depends(get_current_user)):
    return BuildService.get_status()

@build_router.get("/artifacts")
def list_artifacts(project_id: str, user: User = Depends(get_current_user)):
    return BuildService.list_artifacts(project_id)
```

- [ ] **Step 7：更新 api/router.py（最终版本）**

```python
from fastapi import APIRouter
from app.api.auth import auth_router
from app.api.projects import projects_router
from app.api.chat import chat_router
from app.api.documents import doc_router
from app.api.executor import executor_router
from app.api.build import build_router

api_router = APIRouter()
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(doc_router)
api_router.include_router(chat_router)
api_router.include_router(executor_router)
api_router.include_router(build_router)
```

---

### Task 10：前端基础框架

**文件：**
- 新建：`frontend/package.json`
- 新建：`frontend/tsconfig.json`
- 新建：`frontend/tsconfig.node.json`
- 新建：`frontend/vite.config.ts`
- 新建：`frontend/tailwind.config.js`
- 新建：`frontend/postcss.config.js`
- 新建：`frontend/index.html`
- 新建：`frontend/src/main.tsx`
- 新建：`frontend/src/App.tsx`
- 新建：`frontend/src/index.css`
- 新建：`frontend/src/api/client.ts`
- 新建：`frontend/src/store/index.ts`

- [ ] **Step 1：创建 package.json**

```json
{
  "name": "nebula-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.0",
    "zustand": "^4.5.0",
    "@tanstack/react-query": "^5.51.0",
    "react-markdown": "^9.0.1"
  },
  "devDependencies": {
    "@types/react": "^18.3.3",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.19",
    "postcss": "^8.4.39",
    "tailwindcss": "^3.4.6",
    "typescript": "^5.5.3",
    "vite": "^5.4.0"
  }
}
```

- [ ] **Step 2：创建 tsconfig.json**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "isolatedModules": true,
    "moduleDetection": "force",
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "forceConsistentCasingInFileNames": true
  },
  "include": ["src"]
}
```

- [ ] **Step 3：创建 vite.config.ts**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: { '/api': { target: 'http://localhost:8000', changeOrigin: true } },
  },
})
```

- [ ] **Step 4：创建 tailwind.config.js**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: { extend: {} },
  plugins: [],
}
```

- [ ] **Step 5：创建 postcss.config.js**

```javascript
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
```

- [ ] **Step 6：创建 index.html**

```html
<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>星云 · Nebula</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 7：创建 src/index.css**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
body { @apply bg-gray-50 text-gray-900; }
```

- [ ] **Step 8：创建 src/api/client.ts**

```typescript
const API_BASE = '/api/v1';

interface ApiOpts { method?: string; body?: unknown; headers?: Record<string, string> }

async function request<T>(path: string, opts: ApiOpts = {}): Promise<T> {
  const token = localStorage.getItem('nebula_token');
  const headers: Record<string, string> = { 'Content-Type': 'application/json', ...opts.headers };
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(`${API_BASE}${path}`, {
    method: opts.method || 'GET',
    headers,
    body: opts.body ? JSON.stringify(opts.body) : undefined,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: '请求失败' }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

export const api = {
  auth: {
    register: (d: { username: string; email: string; password: string }) =>
      request<{ id: string; username: string }>('/auth/register', { method: 'POST', body: d }),
    login: (d: { username: string; password: string }) =>
      request<{ access_token: string; user: { id: string; username: string; role: string } }>(
        '/auth/login', { method: 'POST', body: d }),
    me: () => request<{ id: string; username: string; role: string; email: string }>('/auth/me'),
  },
  projects: {
    list: () => request<Array<{ id: string; name: string; description: string; created_at: string }>>('/projects'),
    create: (d: { name: string; description?: string }) =>
      request<{ id: string; name: string; description: string }>('/projects', { method: 'POST', body: d }),
    get: (id: string) => request<{ id: string; name: string; description: string }>(`/projects/${id}`),
    delete: (id: string) => request<{ message: string }>(`/projects/${id}`, { method: 'DELETE' }),
  },
  sessions: {
    list: (pid: string) =>
      request<Array<{ id: string; status: string }>>(`/projects/${pid}/sessions`),
    create: (pid: string) =>
      request<{ id: string; project_id: string; status: string }>(
        `/projects/${pid}/sessions`, { method: 'POST' }),
    messages: (pid: string, sid: string) =>
      request<Array<{ id: string; role: string; content: string; phase?: string; created_at: string }>>(
        `/projects/${pid}/sessions/${sid}/messages`),
    send: (pid: string, sid: string, content: string) =>
      request<Array<{ id: string; role: string; content: string; phase?: string; created_at: string }>>(
        `/projects/${pid}/sessions/${sid}/messages`, { method: 'POST', body: { content } }),
  },
  docs: {
    list: (pid: string) => request<Array<{ type: string; exists: boolean }>>(`/projects/${pid}/docs`),
    get: (pid: string, type: string) =>
      request<{ type: string; content: string }>(`/projects/${pid}/docs/${type}`),
    generate: (pid: string) =>
      request<{ success: boolean; message: string }>(`/projects/${pid}/docs/generate`, { method: 'POST' }),
  },
  executor: {
    execute: (pid: string) =>
      request<{ status: string; message?: string }>(`/projects/${pid}/execute`, { method: 'POST' }),
    status: (pid: string) =>
      request<{ status: string; message?: string }>(`/projects/${pid}/execute/status`),
  },
  build: {
    trigger: (pid: string) =>
      request<{ status: string; message?: string }>(`/projects/${pid}/build`, { method: 'POST' }),
    status: (pid: string) =>
      request<{ status: string; message?: string }>(`/projects/${pid}/build/status`),
    artifacts: (pid: string) =>
      request<Array<{ version: string; created_at: string; path: string }>>(`/projects/${pid}/build/artifacts`),
  },
};
```

- [ ] **Step 9：创建 src/store/index.ts**

```typescript
import { create } from 'zustand';

interface User { id: string; username: string; email: string; role: string }

interface AppState {
  user: User | null;
  token: string | null;
  currentProjectId: string | null;
  setAuth: (user: User, token: string) => void;
  logout: () => void;
  setCurrentProject: (id: string | null) => void;
}

export const useStore = create<AppState>((set) => ({
  user: null,
  token: localStorage.getItem('nebula_token'),
  currentProjectId: null,
  setAuth: (user, token) => {
    localStorage.setItem('nebula_token', token);
    set({ user, token });
  },
  logout: () => {
    localStorage.removeItem('nebula_token');
    set({ user: null, token: null, currentProjectId: null });
  },
  setCurrentProject: (id) => set({ currentProjectId: id }),
}));
```

- [ ] **Step 10：创建 src/main.tsx**

```tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import App from './App';
import './index.css';

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter><App /></BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>,
);
```

- [ ] **Step 11：创建 src/App.tsx**

```tsx
import { Routes, Route, Navigate } from 'react-router-dom';
import { useStore } from './store';
import Login from './pages/Login';
import Register from './pages/Register';
import Projects from './pages/Projects';
import Chat from './pages/Chat';
import Docs from './pages/Docs';
import AppLayout from './components/AppLayout';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  return useStore((s) => s.token) ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/projects" element={<ProtectedRoute><AppLayout><Projects /></AppLayout></ProtectedRoute>} />
      <Route path="/projects/:id" element={<ProtectedRoute><AppLayout><Chat /></AppLayout></ProtectedRoute>} />
      <Route path="/projects/:id/docs" element={<ProtectedRoute><AppLayout><Docs /></AppLayout></ProtectedRoute>} />
      <Route path="/" element={<Navigate to="/projects" replace />} />
    </Routes>
  );
}
```

- [ ] **Step 12：安装依赖 + 验证**

```bash
cd frontend && npm install && npx tsc --noEmit
```

预期输出：TypeScript 编译无错误

---

### Task 11：前端 — 登录 + 布局

**文件：**
- 新建：`frontend/src/pages/Login.tsx`
- 新建：`frontend/src/pages/Register.tsx`
- 新建：`frontend/src/components/AppLayout.tsx`
- 新建：`frontend/src/components/Sidebar.tsx`

- [ ] **Step 1：创建 Login.tsx**

```tsx
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../api/client';
import { useStore } from '../store';

export default function Login() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();
  const setAuth = useStore((s) => s.setAuth);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      const res = await api.auth.login({ username, password });
      setAuth(res.user, res.access_token);
      navigate('/projects');
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold text-center mb-2">星云 · Nebula</h1>
        <p className="text-gray-500 text-center mb-6">AI Agent 中台平台</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">用户名</label>
            <input type="text" value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">密码</label>
            <input type="password" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button type="submit"
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700">
            登录
          </button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-500">
          没有账号？<Link to="/register" className="text-blue-600 hover:underline">注册</Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 2：创建 Register.tsx**

```tsx
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { api } from '../api/client';

export default function Register() {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    try {
      await api.auth.register({ username, email, password });
      navigate('/login');
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h1 className="text-2xl font-bold text-center mb-6">注册账号</h1>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">用户名</label>
            <input type="text" value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="mt-1 w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required minLength={2} />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">邮箱</label>
            <input type="email" value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700">密码</label>
            <input type="password" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required minLength={6} />
          </div>
          {error && <p className="text-red-500 text-sm">{error}</p>}
          <button type="submit"
            className="w-full py-2 px-4 bg-blue-600 text-white rounded-md hover:bg-blue-700">
            注册
          </button>
        </form>
        <p className="text-center mt-4 text-sm text-gray-500">
          已有账号？<Link to="/login" className="text-blue-600 hover:underline">登录</Link>
        </p>
      </div>
    </div>
  );
}
```

- [ ] **Step 3：创建 AppLayout.tsx**

```tsx
import Sidebar from './Sidebar';

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-auto">{children}</main>
    </div>
  );
}
```

- [ ] **Step 4：创建 Sidebar.tsx**

```tsx
import { Link, useParams, useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import { useStore } from '../store';

export default function Sidebar() {
  const navigate = useNavigate();
  const params = useParams();
  const { user, logout, setCurrentProject } = useStore();

  const { data: projects } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.projects.list(),
  });

  return (
    <aside className="w-64 bg-gray-900 text-white flex flex-col h-screen">
      <div className="p-4 border-b border-gray-700">
        <h2 className="text-lg font-bold">星云 · Nebula</h2>
        <p className="text-sm text-gray-400">{user?.username} ({user?.role})</p>
      </div>
      <div className="flex-1 overflow-auto p-4">
        <div className="flex justify-between items-center mb-3">
          <h3 className="text-sm font-medium text-gray-300">项目</h3>
          <Link to="/projects" className="text-xs text-blue-400 hover:underline">管理</Link>
        </div>
        {projects?.map((p) => (
          <Link key={p.id} to={`/projects/${p.id}`}
            className={`block px-3 py-2 rounded-md text-sm mb-1 ${
              params.id === p.id ? 'bg-blue-600' : 'hover:bg-gray-700'
            }`}
            onClick={() => setCurrentProject(p.id)}>
            {p.name}
          </Link>
        ))}
      </div>
      <div className="p-4 border-t border-gray-700">
        <button onClick={() => { logout(); navigate('/login'); }}
          className="text-sm text-gray-400 hover:text-white">退出登录</button>
      </div>
    </aside>
  );
}
```

---

### Task 12：前端 — 项目列表 + 对话页

**文件：**
- 新建：`frontend/src/pages/Projects.tsx`
- 新建：`frontend/src/pages/Chat.tsx`
- 新建：`frontend/src/components/MessageBubble.tsx`
- 新建：`frontend/src/components/MessageInput.tsx`
- 新建：`frontend/src/components/ConfirmCard.tsx`
- 新建：`frontend/src/components/StatusBadge.tsx`

- [ ] **Step 1：创建 Projects.tsx**

```tsx
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';

export default function Projects() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [showCreate, setShowCreate] = useState(false);
  const [name, setName] = useState('');
  const [desc, setDesc] = useState('');

  const { data: projects, isLoading } = useQuery({
    queryKey: ['projects'],
    queryFn: () => api.projects.list(),
  });

  const createMut = useMutation({
    mutationFn: (d: { name: string; description?: string }) => api.projects.create(d),
    onSuccess: (p) => {
      qc.invalidateQueries({ queryKey: ['projects'] });
      setShowCreate(false); setName(''); setDesc('');
      navigate(`/projects/${p.id}`);
    },
  });

  const deleteMut = useMutation({
    mutationFn: (id: string) => api.projects.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['projects'] }),
  });

  if (isLoading) return <div className="p-8">加载中...</div>;

  return (
    <div className="p-8">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-bold">项目列表</h1>
        <button onClick={() => setShowCreate(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">
          创建项目
        </button>
      </div>
      {showCreate && (
        <div className="bg-white p-6 rounded-lg shadow-md mb-6">
          <h2 className="text-lg font-semibold mb-4">新建项目</h2>
          <div className="space-y-3">
            <input type="text" placeholder="项目名称" value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border rounded-md" />
            <textarea placeholder="项目描述（可选）" value={desc}
              onChange={(e) => setDesc(e.target.value)} className="w-full px-3 py-2 border rounded-md" rows={3} />
            <div className="flex gap-2">
              <button onClick={() => createMut.mutate({ name, description: desc })}
                disabled={!name}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">
                创建
              </button>
              <button onClick={() => setShowCreate(false)}
                className="px-4 py-2 border rounded-md hover:bg-gray-50">取消</button>
            </div>
          </div>
        </div>
      )}
      {projects?.length === 0 ? (
        <div className="text-center py-16 text-gray-500">
          <p className="text-lg mb-2">还没有项目</p>
          <p>点击「创建项目」开始你的第一个星云项目</p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {projects?.map((p) => (
            <div key={p.id} onClick={() => navigate(`/projects/${p.id}`)}
              className="bg-white p-6 rounded-lg shadow-md cursor-pointer hover:shadow-lg transition-shadow">
              <h3 className="font-semibold text-lg mb-2">{p.name}</h3>
              {p.description && <p className="text-gray-500 text-sm mb-3">{p.description}</p>}
              <div className="flex justify-between items-center">
                <span className="text-xs text-gray-400">{new Date(p.created_at).toLocaleDateString('zh-CN')}</span>
                <button onClick={(e) => { e.stopPropagation(); deleteMut.mutate(p.id); }}
                  className="text-xs text-red-500 hover:underline">删除</button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2：创建 MessageBubble.tsx**

```tsx
import ReactMarkdown from 'react-markdown';

interface Props { role: 'user' | 'agent'; content: string; phase?: string }

const phaseLabels: Record<string, string> = {
  greeting: '👋 问候', collecting: '📋 收集需求',
  clarifying: '🤔 澄清细节', confirming: '✅ 确认范围', generating: '📄 生成文档',
};

export default function MessageBubble({ role, content, phase }: Props) {
  const isUser = role === 'user';
  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      <div className={`max-w-[70%] rounded-lg p-4 ${
        isUser ? 'bg-blue-600 text-white' : 'bg-white border border-gray-200'
      }`}>
        {phase && !isUser && (
          <div className="text-xs text-gray-400 mb-1">{phaseLabels[phase] || phase}</div>
        )}
        {isUser ? <p className="whitespace-pre-wrap">{content}</p> : (
          <div className="prose prose-sm max-w-none"><ReactMarkdown>{content}</ReactMarkdown></div>
        )}
      </div>
    </div>
  );
}
```

- [ ] **Step 3：创建 MessageInput.tsx**

```tsx
import { useState } from 'react';

interface Props { onSend: (content: string) => void; disabled?: boolean }

export default function MessageInput({ onSend, disabled }: Props) {
  const [input, setInput] = useState('');
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || disabled) return;
    onSend(input.trim());
    setInput('');
  };
  return (
    <form onSubmit={handleSubmit} className="border-t bg-white p-4">
      <div className="flex gap-2">
        <input type="text" value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="输入你的需求..." disabled={disabled}
          className="flex-1 px-4 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50" />
        <button type="submit" disabled={!input.trim() || disabled}
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50">
          发送
        </button>
      </div>
    </form>
  );
}
```

- [ ] **Step 4：创建 ConfirmCard.tsx**

```tsx
interface Props {
  summary?: string;
  onConfirm: () => void;
  onRevise: () => void;
}

export default function ConfirmCard({ summary, onConfirm, onRevise }: Props) {
  return (
    <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
      <h3 className="font-semibold text-green-800 mb-2">需求范围确认</h3>
      {summary && (
        <div className="mb-3">
          <p className="text-sm font-medium text-green-700">需求摘要：</p>
          <p className="text-sm text-green-600 whitespace-pre-wrap">{summary}</p>
        </div>
      )}
      <div className="flex gap-2 mt-3">
        <button onClick={onConfirm}
          className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm">
          ✅ 确认，开始生成文档
        </button>
        <button onClick={onRevise}
          className="px-4 py-2 border border-green-300 text-green-700 rounded-md hover:bg-green-100 text-sm">
          ✏️ 需要调整
        </button>
      </div>
    </div>
  );
}
```

- [ ] **Step 5：创建 StatusBadge.tsx**

```tsx
interface Props { status: string }

const conf: Record<string, [string, string]> = {
  idle: ['bg-gray-100', 'text-gray-600'], running: ['bg-blue-100', 'text-blue-600'],
  testing: ['bg-yellow-100', 'text-yellow-600'], verifying: ['bg-yellow-100', 'text-yellow-600'],
  packaging: ['bg-purple-100', 'text-purple-600'], success: ['bg-green-100', 'text-green-600'],
  failed: ['bg-red-100', 'text-red-600'],
};
const labels: Record<string, string> = {
  idle: '等待中', running: '执行中', testing: '测试中',
  verifying: '校验中', packaging: '打包中', success: '已完成', failed: '失败',
};

export default function StatusBadge({ status }: Props) {
  const [bg, text] = conf[status] || ['bg-gray-100', 'text-gray-600'];
  return (
    <span className={`px-2 py-1 rounded-full text-xs font-medium ${bg} ${text}`}>
      {labels[status] || status}
    </span>
  );
}
```

- [ ] **Step 6：创建 Chat.tsx**

```tsx
import { useEffect, useRef, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../api/client';
import MessageBubble from '../components/MessageBubble';
import MessageInput from '../components/MessageInput';
import ConfirmCard from '../components/ConfirmCard';
import StatusBadge from '../components/StatusBadge';

export default function Chat() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const msgEndRef = useRef<HTMLDivElement>(null);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [showConfirm, setShowConfirm] = useState(false);
  const [reqSummary, setReqSummary] = useState('');
  const [execStatus, setExecStatus] = useState('idle');
  const [buildStatus, setBuildStatus] = useState('idle');

  useEffect(() => {
    if (id) api.sessions.create(id).then((s) => setSessionId(s.id));
  }, [id]);

  const { data: messages } = useQuery({
    queryKey: ['messages', sessionId],
    queryFn: () => api.sessions.messages(id!, sessionId!),
    enabled: !!sessionId,
    refetchInterval: 2000,
  });

  const sendMut = useMutation({
    mutationFn: (c: string) => api.sessions.send(id!, sessionId!, c),
    onSuccess: (msgs) => {
      qc.invalidateQueries({ queryKey: ['messages', sessionId] });
      const last = msgs[msgs.length - 1];
      if (last?.phase === 'confirming') { setShowConfirm(true); setReqSummary(last.content); }
      if (last?.phase === 'generating') setShowConfirm(false);
    },
  });

  const handleConfirm = async () => {
    setShowConfirm(false);
    await api.docs.generate(id!);
    sendMut.mutate('确认，没有问题');
  };

  const handleRevise = () => { setShowConfirm(false); sendMut.mutate('需要调整'); };

  useEffect(() => { msgEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  return (
    <div className="flex flex-col h-full">
      <div className="border-b bg-white px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Link to="/projects" className="text-gray-400 hover:text-gray-600">← 返回</Link>
          <h2 className="font-semibold">需求对话</h2>
        </div>
        {messages?.some((m) => m.phase === 'generating') && (
          <div className="flex gap-2">
            <Link to={`/projects/${id}/docs`}
              className="px-3 py-1 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200">
              查看文档
            </Link>
            <button onClick={async () => {
              setExecStatus('running');
              const r = await api.executor.execute(id!);
              setExecStatus(r.status);
            }} className="px-3 py-1 text-sm bg-green-600 text-white rounded-md hover:bg-green-700">
              ⚡ 开始编码
            </button>
          </div>
        )}
      </div>
      <div className="flex-1 overflow-auto p-6 bg-gray-50">
        {messages?.map((m) => (
          <MessageBubble key={m.id} role={m.role as 'user' | 'agent'} content={m.content} phase={m.phase} />
        ))}
        {showConfirm && <ConfirmCard summary={reqSummary} onConfirm={handleConfirm} onRevise={handleRevise} />}
        {execStatus !== 'idle' && (
          <div className="bg-white border rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-sm">🔧 编码执行</span>
              <StatusBadge status={execStatus} />
            </div>
            {execStatus === 'success' && (
              <div className="mt-2">
                <button onClick={async () => {
                  setBuildStatus('running');
                  const r = await api.build.trigger(id!);
                  setBuildStatus(r.status);
                }} className="px-3 py-1 text-sm bg-purple-600 text-white rounded-md">
                  📦 开始构建
                </button>
              </div>
            )}
          </div>
        )}
        {buildStatus !== 'idle' && (
          <div className="bg-white border rounded-lg p-4 mb-4">
            <div className="flex items-center gap-2">
              <span className="text-sm">📦 构建验证</span>
              <StatusBadge status={buildStatus} />
            </div>
            {buildStatus === 'success' && <p className="text-sm text-green-600 mt-2">✅ 构建完成</p>}
          </div>
        )}
        <div ref={msgEndRef} />
      </div>
      <MessageInput onSend={(c) => sendMut.mutate(c)} disabled={showConfirm || execStatus !== 'idle'} />
    </div>
  );
}
```

---

### Task 13：前端 — 文档页

**文件：**
- 新建：`frontend/src/pages/Docs.tsx`
- 新建：`frontend/src/components/DocViewer.tsx`

- [ ] **Step 1：创建 Docs.tsx**

```tsx
import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../api/client';
import DocViewer from '../components/DocViewer';

export default function Docs() {
  const { id } = useParams<{ id: string }>();
  const [selected, setSelected] = useState('proposal');

  const { data: docs } = useQuery({
    queryKey: ['docs', id],
    queryFn: () => api.docs.list(id!),
  });

  const { data: content } = useQuery({
    queryKey: ['doc', id, selected],
    queryFn: () => api.docs.get(id!, selected),
    enabled: !!selected,
  });

  return (
    <div className="flex flex-col h-full">
      <div className="border-b bg-white px-6 py-3">
        <Link to={`/projects/${id}`} className="text-gray-400 hover:text-gray-600 mr-3">← 返回对话</Link>
        <span className="font-semibold">设计文档</span>
      </div>
      <div className="flex flex-1">
        <div className="w-48 border-r bg-gray-50 p-4">
          {docs?.map((d) => (
            <button key={d.type} onClick={() => setSelected(d.type)}
              className={`block w-full text-left px-3 py-2 rounded-md text-sm mb-1 ${
                selected === d.type ? 'bg-blue-100 text-blue-700' : 'hover:bg-gray-200'
              }`}>
              {d.type === 'proposal' && '📋 Proposal'}
              {d.type === 'specs' && '📐 Specs'}
              {d.type === 'design' && '🏗️ Design'}
              {d.type === 'tasks' && '✅ Tasks'}
              {!d.exists && ' ⏳'}
            </button>
          ))}
        </div>
        <div className="flex-1 overflow-auto p-6">
          {content ? <DocViewer content={content.content} /> : <p className="text-gray-400">选择左侧文档查看</p>}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 2：创建 DocViewer.tsx**

```tsx
import ReactMarkdown from 'react-markdown';

interface Props { content: string }

export default function DocViewer({ content }: Props) {
  return <div className="prose prose-sm max-w-none"><ReactMarkdown>{content}</ReactMarkdown></div>;
}
```

---

### Task 14：集成验证

- [ ] **Step 1：运行所有后端测试**

```bash
cd backend && python -m pytest tests/ -v
```

预期结果：所有测试通过

- [ ] **Step 2：启动后端服务**

```bash
cd backend && python seed.py && uvicorn app.main:app --reload
```

预期结果：服务启动在 http://localhost:8000

- [ ] **Step 3：启动前端开发服务**

```bash
cd frontend && npm run dev
```

预期结果：开发服务启动在 http://localhost:5173

- [ ] **Step 4：完整链路手动验证**

1. 打开 http://localhost:5173
2. 注册新账号 → 跳转到登录页
3. 用 admin/123456 登录 → 看到空项目列表
4. 点击"创建项目" → 创建项目
5. 进入项目 → Agent 打招呼
6. 描述需求 → Agent 经历收集/澄清流程
7. 确认范围 → "生成文档"按钮出现
8. 点击生成 → 文档创建完毕
9. 在 /projects/:id/docs 查看文档
10. 点击"开始编码" → Claude Code 执行编码
11. 点击"开始构建" → 构建验证器运行
12. Artifact 产出

- [ ] **Step 5：配置 .env**

```bash
cp .env.example .env
# 修改 JWT_SECRET 为随机值
```
