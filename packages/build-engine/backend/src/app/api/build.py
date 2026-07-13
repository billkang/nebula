from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.build_service import BuildService
from app.services.runtime_client import RuntimeClient
from app.utils.project_path import resolve_project_dir

build_router = APIRouter(prefix="/projects/{project_id}/build", tags=["build"])


@build_router.post("")
def trigger_build(project_id: str, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    project_dir = resolve_project_dir(project_id, db)
    return BuildService().build(project_id, project_dir)


@build_router.get("/status")
def build_status(project_id: str, user: User = Depends(get_current_user)):
    status = BuildService.get_status(project_id)
    # 附加 runtime 状态
    if status.get("runtime_status") == "pushed":
        status["runtime"] = RuntimeClient.get_status(project_id, status.get("artifact_version", ""))
    return status


@build_router.get("/artifacts")
def list_artifacts(project_id: str, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    project_dir = resolve_project_dir(project_id, db)
    return BuildService.list_artifacts(project_dir)


@build_router.post("/deploy")
def deploy_to_runtime(project_id: str, version: str, user: User = Depends(get_current_user)):
    """手动推送并启动指定 Artifact 到 runtime。"""
    available = RuntimeClient.is_available()
    if not available:
        return {"data": None, "error": "Runtime 不可用"}
    try:
        RuntimeClient.push_artifact(project_id, version)
        result = RuntimeClient.start_application(project_id, version)
        return {"data": result, "error": None}
    except Exception as e:
        return {"data": None, "error": str(e)}


@build_router.get("/runtime-status")
def runtime_status(project_id: str, user: User = Depends(get_current_user)):
    """查询 runtime 运行状态。"""
    available = RuntimeClient.is_available()
    if not available:
        return {"data": {"status": "unavailable"}, "error": None}
    try:
        import httpx
        resp = httpx.get(f"{RuntimeClient.runtime_url()}/api/v1/runtime/status", timeout=10)
        status_data = resp.json().get("data", {})
        return {"data": status_data, "error": None}
    except Exception as e:
        return {"data": {"status": "error"}, "error": str(e)}
