from datetime import datetime, timedelta, timezone
from jose import jwt
import bcrypt
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.config import settings
from app.models.user import User, UserRole
from app.schemas.auth import RegisterRequest, LoginRequest, UserResponse


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))


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
