import shutil
import tarfile
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form

from app.services.registry_service import RegistryService, RegistryError

registry_router = APIRouter()


@registry_router.get("/artifacts")
async def list_versions(project_id: str):
    try:
        versions = RegistryService.list_versions(project_id)
        return {"data": versions, "error": None}
    except RegistryError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@registry_router.get("/artifacts/{project_id}/{version}")
async def get_version(project_id: str, version: str):
    try:
        info = RegistryService.get_version(project_id, version)
        return {"data": info, "error": None}
    except RegistryError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)


@registry_router.post("/artifacts/{project_id}")
async def register_artifact(
    project_id: str,
    file: UploadFile = File(...),
):
    """Register a new artifact version. Accepts a tar.gz file upload."""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp_path = Path(tmpdir) / "artifact.tar.gz"
            with open(tmp_path, "wb") as f:
                content = await file.read()
                f.write(content)

            extract_dir = Path(tmpdir) / "extracted"
            extract_dir.mkdir()
            with tarfile.open(tmp_path, "r:gz") as tar:
                tar.extractall(path=extract_dir)

            result = RegistryService.register_artifact(project_id, str(extract_dir))
            return {"data": result, "error": None}
    except RegistryError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except tarfile.ReadError:
        raise HTTPException(status_code=400, detail="Invalid tar.gz file")


@registry_router.delete("/artifacts/{project_id}/{version}")
async def delete_version(project_id: str, version: str):
    try:
        result = RegistryService.delete_version(project_id, version)
        return {"data": result, "error": None}
    except RegistryError as e:
        raise HTTPException(status_code=e.status_code, detail=e.message)
