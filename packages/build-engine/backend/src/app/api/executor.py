from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.executor_service import ExecutorService
from app.utils.project_path import resolve_project_dir

executor_router = APIRouter(prefix="/projects/{project_id}/execute", tags=["executor"])


@executor_router.post("")
def execute(project_id: str, db: Session = Depends(get_db),
            user: User = Depends(get_current_user)):
    project_dir = resolve_project_dir(project_id, db)
    svc = ExecutorService()
    return svc.execute(project_id, project_dir)


@executor_router.get("/status")
def execute_status(project_id: str, user: User = Depends(get_current_user)):
    return ExecutorService.get_status(project_id)
