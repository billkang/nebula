from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.services.container_service import ContainerService
from app.services.registry_service import RegistryService, RegistryError

runtime_router = APIRouter()


class StartRequest(BaseModel):
    project_id: str
    version: str


class PushRequest(BaseModel):
    project_id: str
    source_dir: str


@runtime_router.post("/start")
async def start_application(req: StartRequest):
    """Load artifact, build Docker image, start container."""
    artifact_path = RegistryService.get_artifact_path(req.project_id, req.version)
    if artifact_path is None:
        raise HTTPException(status_code=404, detail=f"Artifact {req.version} not found")

    try:
        result = ContainerService.start(artifact_path, req.project_id, req.version)
        return {"data": result, "error": None}
    except RegistryError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@runtime_router.post("/stop")
async def stop_application():
    """Stop the currently running application."""
    try:
        result = ContainerService.stop()
        return {"data": result, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@runtime_router.get("/status")
async def application_status():
    """Query running status of the application."""
    status = ContainerService.status()
    return {"data": status, "error": None}


@runtime_router.get("/logs")
async def application_logs(tail: int = 100):
    """Get recent logs from the running application."""
    logs = ContainerService.logs(tail)
    return {"data": logs, "error": None}


@runtime_router.post("/push")
async def push_artifact(req: PushRequest):
    """Register an artifact from platform build output directory."""
    try:
        result = RegistryService.register_artifact(req.project_id, req.source_dir)
        return {"data": result, "error": None}
    except RegistryError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@runtime_router.get("/versions")
async def list_versions(project_id: str):
    """List available artifact versions."""
    versions = RegistryService.list_versions(project_id)
    return {"data": versions, "error": None}
