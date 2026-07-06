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
