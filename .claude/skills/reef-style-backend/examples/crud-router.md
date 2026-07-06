# 示例：FastAPI CRUD Router

```python
# app/api/v1/users.py
from fastapi import APIRouter, Depends, Query, HTTPException
from app.schemas.users import (
    CreateUserRequest,
    UpdateUserRequest,
    UserResponse,
    UserListResponse,
)
from app.services.users import UserService

router = APIRouter(prefix="/api/v1/users", tags=["users"])


@router.get("/", response_model=UserListResponse)
async def list_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    user_service: UserService = Depends(),
):
    """获取用户列表"""
    users, total = await user_service.list_users(skip=skip, limit=limit)
    return UserListResponse(items=users, total=total, skip=skip, limit=limit)


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: int,
    user_service: UserService = Depends(),
):
    """获取单个用户"""
    user = await user_service.get_user(user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.post("/", response_model=UserResponse, status_code=201)
async def create_user(
    request: CreateUserRequest,
    user_service: UserService = Depends(),
):
    """创建用户"""
    return await user_service.create_user(request)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    request: UpdateUserRequest,
    user_service: UserService = Depends(),
):
    """更新用户"""
    user = await user_service.update_user(user_id, request)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    user_service: UserService = Depends(),
):
    """删除用户"""
    deleted = await user_service.delete_user(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="User not found")
```
