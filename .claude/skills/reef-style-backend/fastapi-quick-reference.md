# FastAPI 最佳实践

## 路由组织

```python
# ✅ 好：按领域分组路由
# app/api/v1/users.py
router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/", response_model=list[UserResponse])
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_service: UserService = Depends(),
):
    return await user_service.list_users(skip=skip, limit=limit)
```

**规范：**
- 每个模块一个 `APIRouter`，在 `app/api/v1/__init__.py` 中 `include_router`
- 路径用 kebab-case：`/api/v1/user-roles`，不用 `/api/v1/userRoles`
- 路径变量用 snake_case：`/api/v1/users/{user_id}`
- 列表接口**必须**有分页参数

## 依赖注入

```python
# ✅ 好：用 Depends() 隐式注入
@app.get("/users/{user_id}")
async def get_user(
    user_id: int,
    user_service: UserService = Depends(),
):
    return await user_service.get_user(user_id)

# ❌ 坏：在 Router 中直接实例化 Service
@app.get("/users/{user_id}")
async def get_user(user_id: int):   # ← 没有依赖注入
    service = UserService()          # ← 手动实例化
    return await service.get_user(user_id)
```

**规范：**
- Service 类使用 `__init__` 接收依赖，注册为 `Depends()`
- 不要用全局单例模式
- DAO / Repository 也通过 `Depends()` 注入到 Service

## Pydantic Schema

```python
# ✅ 好：Request / Response Schema 分开
class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    role: UserRole = UserRole.USER

class UserResponse(BaseModel):
    id: int
    name: str
    email: EmailStr
    role: UserRole
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)  # ORM 模式
```

**规范：**
- Request Schema 用 `BaseModel`，加输入约束
- Response Schema 用 `ConfigDict(from_attributes=True)` 以支持 ORM 序列化
- CRUD 接口用 `Create*Request` / `Update*Request` / `*Response` 命名

## 全局异常处理器

```python
# ✅ 好：统一注册
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content={"code": exc.code, "message": exc.detail},
    )
```

## 异步配置

```python
# ✅ 好：FastAPI 原生异步
@app.get("/health")
async def health():
    # 异步 HTTP 调用
    async with httpx.AsyncClient() as client:
        resp = await client.get("https://status.example.com")
    return {"status": "ok"}
```

**红线：** `async def` handler 内部不得调同步的 `time.sleep()` / `requests.get()` / 同步 ORM 操作。需要调同步操作时用 `asyncio.to_thread()` 包裹。
