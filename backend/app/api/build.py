from fastapi import APIRouter, Depends
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.build_service import BuildService

build_router = APIRouter(prefix="/projects/{project_id}/build", tags=["build"])


@build_router.post("")
def trigger_build(project_id: str, user: User = Depends(get_current_user)):
    return BuildService.build(project_id)


@build_router.get("/status")
def build_status(project_id: str, user: User = Depends(get_current_user)):
    return BuildService.get_status(project_id)


@build_router.get("/artifacts")
def list_artifacts(project_id: str, user: User = Depends(get_current_user)):
    return BuildService.list_artifacts(project_id)
