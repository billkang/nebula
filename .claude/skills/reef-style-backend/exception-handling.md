# 异常处理规范（Python / FastAPI）

## 速查

| 场景 | 决策 |
| --- | --- |
| 业务异常 | 继承 `AppError(HTTPException)`，含 `code` + `status_code` + `detail` |
| 全局捕获 | `@app.exception_handler(AppError)` 统一处理 |
| 错误响应 | `{"code": "USER_001", "message": "...", "detail": {}}` |
| 错误码 | `{MODULE}_{NNN}` 枚举 |
| 参数校验失败 | FastAPI 自动处理 `RequestValidationError` |
| 未知异常 | 兜底 500 — `GENERIC_001`，记录完整 traceback |
| Service 层异常 | 抛出 `AppError` 子类，不在 Router 中 try-catch |

## 核心规范

### 业务异常继承层次

```
HTTPException (fastapi)
└── AppError                    ← 抽象基类
    ├── NotFoundError           (404)
    ├── ConflictError           (409)
    ├── ValidationError         (400)
    ├── PermissionError         (403)
    └── FailedPreconditionError (400)
```

```python
from fastapi import HTTPException
from starlette.status import *

class AppError(HTTPException):
    """业务异常基类。所有业务异常必须继承此类。"""
    def __init__(self, status_code: int, code: str, message: str, detail: dict | None = None):
        super().__init__(status_code=status_code, detail={
            "code": code,
            "message": message,
            "detail": detail or {},
        })

# 子类
class NotFoundError(AppError):
    def __init__(self, code: str, resource_type: str, resource_id: any):
        super().__init__(
            status_code=HTTP_404_NOT_FOUND,
            code=code,
            message=f"{resource_type} not found: {resource_id}",
            detail={"resource_type": resource_type, "resource_id": resource_id},
        )

class ConflictError(AppError):
    def __init__(self, code: str, message: str):
        super().__init__(status_code=HTTP_409_CONFLICT, code=code, message=message)

class ValidationError(AppError):
    def __init__(self, code: str, message: str, errors: list[dict] | None = None):
        super().__init__(
            status_code=HTTP_400_BAD_REQUEST,
            code=code,
            message=message,
            detail={"errors": errors} if errors else {},
        )

class PermissionDeniedError(AppError):
    def __init__(self, code: str = "AUTH_201", message: str = "无权限访问"):
        super().__init__(status_code=HTTP_403_FORBIDDEN, code=code, message=message)
```

### 错误码枚举

```python
from enum import Enum

class ErrorCode(str, Enum):
    # User — 001~099 输入验证, 100~199 资源状态, 200~299 权限
    USER_001 = "USER_001"    # 用户名已存在
    USER_002 = "USER_002"    # 邮箱格式无效
    USER_100 = "USER_100"    # 用户不存在
    USER_101 = "USER_101"    # 用户已禁用
    USER_200 = "USER_200"    # 无权操作该用户

    # Order
    ORDER_001 = "ORDER_001"  # 订单金额无效
    ORDER_100 = "ORDER_100"  # 订单不存在
    ORDER_101 = "ORDER_101"  # 订单状态不允许操作

    # Auth
    AUTH_001 = "AUTH_001"    # Token 已过期
    AUTH_002 = "AUTH_002"    # Token 无效
    AUTH_201 = "AUTH_201"    # 无权限访问

    # Generic
    GENERIC_001 = "GENERIC_001"  # 系统内部错误
    GENERIC_404 = "GENERIC_404"  # 接口不存在
```

### 全局异常处理器

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

app = FastAPI()


# ✅ 业务异常统一处理
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.detail,
    )


# ✅ FastAPI 参数校验失败（Pydantic 校验）
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errors = [
        {"field": err["loc"][-1], "message": err["msg"]}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=422,
        content={
            "code": "VALIDATION_001",
            "message": "参数校验失败",
            "detail": {"errors": errors},
        },
    )


# ✅ 兜底：未捕获异常 → 500
@app.exception_handler(Exception)
async def unexpected_error_handler(request: Request, exc: Exception):
    logger.error("Unexpected error", exc_info=True)  # 完整 traceback 只打日志
    return JSONResponse(
        status_code=500,
        content={
            "code": "GENERIC_001",
            "message": "系统内部错误",
            "detail": {},
        },
    )
```

**规范：**
- 不要在 Router 函数中写 try-except 包裹业务逻辑
- 不要吞异常后返回 `None` 或空字典
- 兜底 handler 必须 `logger.error(..., exc_info=True)`
- `RequestValidationError` 的 detail 中返回具体字段错误信息

### 异常使用示例

```python
# Service 层 — 直接抛异常
class UserService:
    async def get_user(self, user_id: int) -> UserResponse:
        user = await user_repository.get_by_id(user_id)
        if user is None:
            raise NotFoundError(ErrorCode.USER_100, "User", user_id)
        return UserResponse.from_orm(user)

    async def create_user(self, request: CreateUserRequest) -> UserResponse:
        existing = await user_repository.get_by_email(request.email)
        if existing:
            raise ConflictError(ErrorCode.USER_001, "邮箱已注册")
        user = await user_repository.create(request)
        return UserResponse.from_orm(user)

# Router 层 — 不需要 try-catch
@router.post("", response_model=ApiResponse[UserResponse])
async def create_user(request: CreateUserRequest, user_service: UserService = Depends()):
    user = await user_service.create_user(request)
    return ApiResponse.success(user)
```
