# API 规范（Python / FastAPI）

## 速查

| 场景 | 决策 |
| --- | --- |
| 资源路径 | 英文复数 kebab-case：`/api/v1/user-roles`，不用 camelCase |
| 路径变量 | snake_case：`/api/v1/users/{user_id}` |
| 自定义动作 | 遵循 REST 语义；无法用标准 CRUD 时用 `@router.post("/{id}:action")` |
| 查询参数 | snake_case：`?status=active&page=1&page_size=20` |
| 统一响应体 | `response_model` + `ApiResponse[T]` / `PageResponse[T]` 包装 |
| 版本策略 | URL path 前缀 `/api/v1/` |
| 错误响应 | 统一 JSON：`{"code": "USER_001", "message": "...", "detail": {}}` |
| OpenAPI | FastAPI 自动生成，配合 `summary` / `description` / `tags` |
| 分页 | `page`(1-based) + `page_size`(默认 20，最大 100) |

## 核心规范

### 资源命名

- **资源用复数**：`/users`、`/orders`
- **嵌套资源**：`/apps/{app_id}/users/{user_id}`
- **路径 kebab-case**：/api/v1/user-roles，不是 `/api/v1/userRoles`
- **路径参数 snake_case**：`{user_id}`，不是 `{userId}`
- **查询参数 snake_case**：`created_before`、`sort_by`

### 统一响应体

```python
from pydantic import BaseModel
from typing import Generic, TypeVar, List, Optional

T = TypeVar("T")


# ✅ 单资源响应
class ApiResponse(BaseModel, Generic[T]):
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None

    @staticmethod
    def success(data: T) -> "ApiResponse[T]":
        return ApiResponse(success=True, data=data)

    @staticmethod
    def message(msg: str) -> "ApiResponse[T]":
        return ApiResponse(success=True, message=msg)


# ✅ 分页响应
class PageResponse(BaseModel, Generic[T]):
    items: List[T]
    page: int
    page_size: int
    total: int
    total_pages: int


# ✅ 错误响应
class ErrorResponse(BaseModel):
    code: str
    message: str
    detail: dict = {}
```

```python
# ✅ 好：统一响应
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/users", tags=["users"])

@router.get("/{user_id}", response_model=ApiResponse[UserResponse])
async def get_user(user_id: int, user_service: UserService = Depends()):
    user = await user_service.get_user(user_id)
    return ApiResponse.success(user)

@router.get("", response_model=PageResponse[UserResponse])
async def list_users(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    user_service: UserService = Depends(),
):
    return await user_service.list_users(page=page, page_size=page_size)

# ❌ 坏：直接返回实体
@router.get("/{user_id}")
async def get_user(user_id: int):
    return await user_service.get_user(user_id)  # ← 未包装，格式不一致
```

### 版本策略

```python
# ✅ 好：按版本分组
# app/api/v1/users.py
router_v1 = APIRouter(prefix="/api/v1/users", tags=["users-v1"])

# app/api/v2/users.py
router_v2 = APIRouter(prefix="/api/v2/users", tags=["users-v2"])
```

- **非破坏性变更**（新增字段、新增可选参数）：停留在当前版本
- **破坏性变更**（重命名字段、删除字段）：创建 `/api/v2/...`
- **废弃端点**：`@router.get("/...", deprecated=True)`

### 分页约定

```python
# ✅ 好：标准分页
class PaginationParams:
    """分页参数依赖注入"""
    def __init__(
        self,
        page: int = Query(1, ge=1, description="页码（从1开始）"),
        page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    ):
        self.page = page
        self.page_size = page_size
        self.offset = (page - 1) * page_size

@router.get("", response_model=PageResponse[UserResponse])
async def list_users(
    pagination: PaginationParams = Depends(),
    user_service: UserService = Depends(),
):
    items, total = await user_service.list_users(
        skip=pagination.offset, limit=pagination.page_size
    )
    return PageResponse(
        items=items, page=pagination.page,
        page_size=pagination.page_size, total=total,
        total_pages=-(-total // pagination.page_size),  # ceil division
    )
```

### OpenAPI 文档

FastAPI 自动基于 Pydantic model + 路由生成 OpenAPI。额外配置：

```python
# ✅ 好：在路由上添加接口描述
@router.get(
    "/{user_id}",
    summary="获取用户详情",
    description="根据用户 ID 获取完整的用户信息",
    response_model=ApiResponse[UserResponse],
    responses={
        404: {"description": "用户不存在", "model": ErrorResponse},
        403: {"description": "无权限", "model": ErrorResponse},
    },
)
async def get_user(user_id: int, ...):
    ...

# ✅ 好：全局 OpenAPI 元信息
app = FastAPI(
    title="My App API",
    description="用户管理系统 API",
    version="1.0.0",
    docs_url="/api/docs" if settings.ENV != "production" else None,
    redoc_url=None,
)
```
