# 示例：Pydantic Schema

```python
# app/schemas/user.py
from datetime import datetime
from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from app.models.user import UserRole


# ── Request Schemas ──

class CreateUserRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="用户名")
    email: EmailStr = Field(..., description="邮箱")
    password: str = Field(..., min_length=8, max_length=128, description="密码")
    role: UserRole = Field(default=UserRole.USER, description="角色")


class UpdateUserRequest(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    role: Optional[UserRole] = None


# ── Response Schemas ──

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}  # ORM 模式


class UserListResponse(BaseModel):
    items: list[UserResponse]
    total: int
    skip: int
    limit: int
```
