from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user, require_admin
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
def get_project(project_id: int, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    return ProjectService.get_project(project_id, db, user)


@projects_router.delete("/{project_id}")
def delete_project(project_id: int, db: Session = Depends(get_db),
                   user: User = Depends(require_admin)):
    ProjectService.delete_project(project_id, db)
    return {"message": "项目已删除"}
