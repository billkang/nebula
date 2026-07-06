# 安全红线（Python / FastAPI）

## 🔴 红线速查

| 红线 | 禁止行为 | 正确做法 | 违反后果 |
|------|---------|---------|---------|
| 密码存储 | 明文存储密码 | `hashlib` / `bcrypt` / `passlib` 哈希后存储 | P0 — 安全漏洞 |
| SQL 拼接 | f-string / format 拼接 SQL | SQLAlchemy ORM 或 参数化查询 | P0 — SQL 注入 |
| 硬编码密钥 | 代码中硬编码 Secret / Token | 环境变量 `os.getenv()` 或 `pydantic-settings` | P0 — 凭据泄露 |
| 敏感信息打印 | `print()` 敏感数据 | `logging` + 脱敏 + 生产级别过滤 | P1 — 信息泄露 |
| 输入验证缺失 | 不验证用户输入 | Pydantic model + 严格约束 | P1 — 注入/越权 |
| 不安全的 CORS | `allow_origins=["*"]` | 明确指定允许源列表 | P1 — CORS 安全 |
| 调试接口 | 生产暴露 `/docs` / 调试路由 | 根据环境变量控制开启 | P1 — 信息泄露 |

## 🔴 红线详情

### 1. 密码存储 — 禁止明文 （P0）

```python
# ❌ 坏：明文存储
user.password = request.password

# ✅ 好：哈希后存储
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class UserService:
    def create_user(self, request: CreateUserRequest) -> User:
        hashed = pwd_context.hash(request.password)
        user = User(email=request.email, hashed_password=hashed)
        return await user_repository.save(user)

    def verify_password(self, plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

# 验证密码
is_valid = pwd_context.verify(plain_password, user.hashed_password)
```

### 2. SQL 拼接 — 禁止字符串拼接 （P0）

```python
# ❌ 坏：f-string 拼接 — SQL 注入
query = f"SELECT * FROM users WHERE email = '{email}'"
result = await db.execute(query)

# ❌ 坏：format 拼接
query = "SELECT * FROM users WHERE email = '{}'".format(email)
result = await db.execute(query)

# ✅ 好：SQLAlchemy ORM（首选）
user = await db.query(User).filter(User.email == email).first()

# ✅ 好：参数化查询（原生 SQL 时）
from sqlalchemy import text
query = text("SELECT * FROM users WHERE email = :email")
result = await db.execute(query, {"email": email})

# ✅ 好：原始 SQL 用 bind 参数
cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
```

**红线规则：**
- 禁止在 SQL 中使用 `f"..."` 或 `"".format()` 拼接用户输入
- 优先使用 SQLAlchemy ORM 的查询构建器
- 必须使用原生 SQL 时，必须使用参数化查询（`:name` 或 `%s`）

### 3. 硬编码密钥 — 禁止代码中内联 （P0）

```python
# ❌ 坏：硬编码 Secret
SECRET_KEY = "sk-abc123..."
API_KEY = "my-secret-key-12345"

# ✅ 好：pydantic-settings 从环境变量读取
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    secret_key: str
    api_key: str
    database_url: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )

settings = Settings()  # 从 .env 或环境变量加载
```

```bash
# ❌ 坏：提交到 Git 的配置文件中有明文密钥
# config.py
SECRET_KEY = "my-secret-key"  # ← 硬编码

# ✅ 好：.env 本地开发（不提交 Git）
SECRET_KEY=my-secret-key
API_KEY=sk-abc123...
DATABASE_URL=postgresql://localhost:5432/dev

# ✅ 好：CI/CD 中使用 CI Secrets 或 Vault
# GitHub Actions Secrets / GitLab CI Variables
```

### 4. 敏感脱敏 — 日志中禁止打印敏感信息 （P1）

```python
import logging

logger = logging.getLogger(__name__)


# ❌ 坏：直接打印敏感信息
logger.info(f"User login: {email}, password: {password}")  # ← 密码泄露
logger.info(f"Token: {token}")                               # ← Token 泄露
print(f"Auth token: {token}")                                # ← 禁止 print

# ✅ 好：脱敏后打印
def mask_email(email: str) -> str:
    at = email.find("@")
    if at <= 1:
        return email
    return email[0] + "***" + email[at:]

def mask_phone(phone: str) -> str:
    if not phone or len(phone) < 7:
        return phone
    return phone[:3] + "****" + phone[-4:]

logger.info(f"User login: {mask_email(email)}")
logger.info(f"User [id={user_id}] logged in")
```

**红线规则：**
- 禁止打印密码、Token、完整手机号、完整身份证号
- 响应体中密码字段不输出（Pydantic `model_config` 排除或 response schema 中忽略）
- 禁止 `print()` — 必须使用 `logging` 模块

### 5. 输入验证红线 （P1）

```python
# ✅ 好：Pydantic model 严格约束
from pydantic import BaseModel, Field, EmailStr, field_validator

class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    age: int = Field(..., ge=0, le=150)
    role: UserRole = UserRole.USER

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("名称不能为纯空格")
        return v.strip()

# ❌ 坏：不验证或用裸 dict
@app.post("/users")
async def create_user(name: str, email: str):  # ← 无约束
    ...

# ✅ 好：Router 中必须使用 Pydantic model
@app.post("/users", response_model=ApiResponse[UserResponse])
async def create_user(request: CreateUserRequest, ...):
    ...
```

### 6. CORS 配置红线 （P1）

```python
# ❌ 坏：允许所有来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],        # ← 生产环境禁止
    allow_credentials=True,     # ← allow_origins=["*"] 时配合 allow_credentials=True 无效且不安全
)

# ✅ 好：明确指定允许的来源
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://app.example.com",
        "https://admin.example.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)
```

### 7. 生产环境禁用调试接口 （P1）

```python
# ✅ 好：根据环境控制
from app.core.config import settings

app = FastAPI(
    title="My App",
    docs_url="/api/docs" if settings.ENV != "production" else None,
    redoc_url=None,
)

# ❌ 坏：生产环境也暴露
app = FastAPI(docs_url="/api/docs")  # ← 生产环境暴露 API 文档
```
