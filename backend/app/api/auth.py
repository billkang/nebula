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
