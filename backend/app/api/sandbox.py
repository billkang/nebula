from fastapi import APIRouter, Depends, HTTPException
from app.middleware.auth import get_current_user
from app.models.user import User
from app.services.sandbox_service import SandboxService

sandbox_router = APIRouter(prefix="/projects/{project_id}/sandbox", tags=["sandbox"])


@sandbox_router.post("/init")
def init_sandbox(
    project_id: str,
    artifact_version: str | None = None,
    user: User = Depends(get_current_user),
):
    """初始化沙箱：从 Artifact 复制源码到沙箱工作区。"""
    try:
        result = SandboxService.init_sandbox(project_id, artifact_version)
        return {"data": result, "error": None}
    except (ValueError, FileNotFoundError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@sandbox_router.get("/files")
def get_sandbox_files(
    project_id: str,
    user: User = Depends(get_current_user),
):
    """获取沙箱工作区文件树。"""
    files = SandboxService.get_sandbox_files(project_id)
    meta = SandboxService._sandbox_meta(project_id)
    return {"data": {"files": files, "meta": meta}, "error": None}


@sandbox_router.get("/files/{file_path:path}")
def get_file(
    project_id: str,
    file_path: str,
    user: User = Depends(get_current_user),
):
    """读取沙箱工作区文件内容。"""
    try:
        content = SandboxService.get_file_content(project_id, file_path)
        return {"data": {"path": file_path, "content": content}, "error": None}
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@sandbox_router.put("/files/{file_path:path}")
def save_file(
    project_id: str,
    file_path: str,
    body: dict,
    user: User = Depends(get_current_user),
):
    """保存文件到沙箱工作区。"""
    content = body.get("content")
    if content is None:
        raise HTTPException(status_code=400, detail="缺少 content 字段")
    try:
        result = SandboxService.save_file(project_id, file_path, content)
        return {"data": result, "error": None}
    except (FileNotFoundError, ValueError, OSError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@sandbox_router.post("/snapshots")
def create_snapshot(
    project_id: str,
    body: dict = {},
    user: User = Depends(get_current_user),
):
    """创建当前工作区的快照。"""
    description = body.get("description", "")
    try:
        result = SandboxService.create_snapshot(project_id, description)
        return {"data": result, "error": None}
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))


@sandbox_router.get("/snapshots")
def get_snapshots(
    project_id: str,
    user: User = Depends(get_current_user),
):
    """列出所有快照。"""
    snapshots = SandboxService.get_snapshots(project_id)
    return {"data": snapshots, "error": None}


@sandbox_router.post("/restore/{snapshot_id}")
def restore_snapshot(
    project_id: str,
    snapshot_id: str,
    user: User = Depends(get_current_user),
):
    """从指定快照恢复工作区。"""
    try:
        result = SandboxService.restore_from_snapshot(project_id, snapshot_id)
        return {"data": result, "error": None}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))


@sandbox_router.get("/diff/{file_path:path}")
def get_diff(
    project_id: str,
    file_path: str,
    user: User = Depends(get_current_user),
):
    """计算文件的修改 diff（当前工作区 vs 原始 Artifact）。"""
    try:
        result = SandboxService.get_diff(project_id, file_path)
        return {"data": result, "error": None}
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@sandbox_router.post("/restore-original")
def restore_original(
    project_id: str,
    body: dict = {},
    user: User = Depends(get_current_user),
):
    """从原始 Artifact 恢复文件。POST body 可选 {file_path: "src/main.py"} 恢复单个文件，
    不传 file_path 则恢复全部文件到沙箱。"""
    file_path = body.get("file_path")
    try:
        result = SandboxService.restore_original(project_id, file_path)
        return {"data": result, "error": None}
    except (FileNotFoundError, ValueError) as e:
        raise HTTPException(status_code=400, detail=str(e))


@sandbox_router.post("/rebuild")
def trigger_rebuild(
    project_id: str,
    body: dict = {},
    user: User = Depends(get_current_user),
):
    """触发重建：自动快照 → 从沙箱构建 → 推送到 runtime。
    如 {async: true} 则在后台线程运行，前端通过 GET /status 轮询。
    """
    description = body.get("description", "")
    async_build = body.get("async", False)
    try:
        result = SandboxService.trigger_rebuild(project_id, description, async_build=async_build)
        return {"data": result, "error": None}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@sandbox_router.get("/rebuild/status")
def get_rebuild_status(
    project_id: str,
    user: User = Depends(get_current_user),
):
    """获取异步重建的当前状态。"""
    from app.services.build_service import BuildService
    result = BuildService.get_async_build_result(project_id)
    return {"data": result, "error": None}


@sandbox_router.post("/rebuild/cancel")
def cancel_rebuild(
    project_id: str,
    user: User = Depends(get_current_user),
):
    """取消正在进行的重建。"""
    from app.services.build_service import BuildService
    result = BuildService.cancel_build(project_id)
    return {"data": result, "error": None}
