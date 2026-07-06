from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.executor_service import ExecutorService

executor_router = APIRouter(prefix="/projects/{project_id}/execute", tags=["executor"])


@executor_router.post("")
def execute(project_id: str, user: User = Depends(get_current_user)):
    return ExecutorService.execute(project_id)


@executor_router.get("/status")
def execute_status(project_id: str, user: User = Depends(get_current_user)):
    return ExecutorService.get_status(project_id)
