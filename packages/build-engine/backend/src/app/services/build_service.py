import json
import threading
from pathlib import Path
from typing import Optional

from app.config import settings
from app.services.coder_backend import CoderBackend
from app.services.backends import create_backend
from app.core.logging import biz_stage_start, biz_stage_end, biz_step

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

_build_states: dict[str, dict] = {}
_async_builds: dict[str, dict] = {}
_async_builds_lock = threading.Lock()


def _build_running_in_thread(project_id: str):
    try:
        result = BuildService().build(project_id)
        with _async_builds_lock:
            if project_id in _async_builds:
                _async_builds[project_id]["result"] = result
                _async_builds[project_id]["done"] = True
    except Exception as e:
        with _async_builds_lock:
            if project_id in _async_builds:
                _async_builds[project_id]["result"] = {"status": "failed", "message": str(e)[:500]}
                _async_builds[project_id]["done"] = True


class BuildService:
    def __init__(self, backend: Optional[CoderBackend] = None):
        self._backend = backend or create_backend()

    @staticmethod
    def _state(project_id: str) -> dict:
        if project_id not in _build_states:
            _build_states[project_id] = {"status": "idle", "message": ""}
        return _build_states[project_id]

    @staticmethod
    def verify_integrity(project_dir: Path) -> list[str]:
        missing = []
        for item in ["src", "requirements.txt", "Dockerfile"]:
            if not (project_dir / item).exists():
                missing.append(item)
        return missing

    def build(self, project_id: str, source_dir: str | None = None) -> dict:
        biz_stage_start("CODE_GEN", project_id=project_id)
        st = BuildService._state(project_id)
        project_dir = Path(source_dir) if source_dir else BASE_DIR / "projects" / project_id

        if BuildService._check_cancelled(project_id):
            biz_stage_end("CODE_GEN", status="cancelled", project_id=project_id)
            return BuildService.get_status(project_id)

        # ── 阶段 1-2: 构建容器内测试 + 验证 + 打包 ──
        st["status"] = "testing"
        st["message"] = "正在构建容器中运行测试和打包..."
        biz_step("CODE_GEN", "container-build")

        version = BuildService._next_version(project_id)
        biz_step("CODE_GEN", "next-version", version=version)

        try:
            build_result = self._backend.execute_build(
                project_dir=str(project_dir),
                version=version,
            )
        except Exception as e:
            st["status"] = "failed"
            st["message"] = f"构建容器执行异常: {str(e)[:500]}"
            biz_stage_end("CODE_GEN", status="failed", reason="container_exception", project_id=project_id)
            return BuildService.get_status(project_id)

        if build_result.status != "success":
            st["status"] = "failed"
            st["message"] = build_result.message or "构建失败"
            st["test_output"] = build_result.test_output
            biz_stage_end("CODE_GEN", status="failed", reason="build_failed", message=build_result.message)
            return BuildService.get_status(project_id)

        # ── 阶段 3: 宿主机端二次确认完整性 ──
        if BuildService._check_cancelled(project_id):
            biz_stage_end("CODE_GEN", status="cancelled", project_id=project_id)
            return BuildService.get_status(project_id)
        st["status"] = "verifying"
        st["message"] = "验证构建产物..."
        biz_step("CODE_GEN", "verify-artifacts")

        missing = BuildService.verify_integrity(project_dir)
        if missing:
            st["status"] = "failed"
            st["message"] = f"缺少必要文件: {', '.join(missing)}"
            biz_stage_end("CODE_GEN", status="failed", reason="integrity_check_failed", missing=missing)
            return BuildService.get_status(project_id)

        # ── 阶段 4: 推送 runtime ──
        if BuildService._check_cancelled(project_id):
            biz_stage_end("CODE_GEN", status="cancelled", project_id=project_id)
            return BuildService.get_status(project_id)

        st["status"] = "success"
        st["message"] = f"构建完成，Artifact: {build_result.artifact_path}"
        st["artifact_version"] = build_result.version or version
        biz_step("CODE_GEN", "push-runtime", version=st["artifact_version"])

        try:
            from app.services.runtime_client import RuntimeClient
            if RuntimeClient.is_available():
                RuntimeClient.push_artifact(project_id, st["artifact_version"])
                RuntimeClient.start_application(project_id, st["artifact_version"])
                st["runtime_status"] = "pushed"
                st["preview_url"] = f"{settings.runtime_url}/preview/{project_id}"
            else:
                st["runtime_status"] = "runtime_unavailable"
        except Exception as e:
            st["runtime_status"] = f"push_failed: {str(e)[:200]}"

        runtime_status = st.get("runtime_status", "")
        if "push_failed" in runtime_status:
            biz_stage_end("CODE_GEN", status="failed", reason="runtime_push_failed",
                          project_id=project_id, version=st.get("artifact_version"))
        else:
            biz_stage_end("CODE_GEN", status="ok", project_id=project_id,
                          version=st.get("artifact_version"))
        return BuildService.get_status(project_id)

    @staticmethod
    def _next_version(project_id: str) -> str:
        existing = BuildService.list_artifacts(project_id)
        max_num = 0
        for v in existing:
            vname = v["version"]
            if vname.startswith("v") and vname[1:].isdigit():
                num = int(vname[1:])
                if num > max_num:
                    max_num = num
        return f"v{max_num + 1}"

    @staticmethod
    def _check_cancelled(project_id: str) -> dict | None:
        st = BuildService._state(project_id)
        if st.get("cancel_requested"):
            st["status"] = "cancelled"
            st["message"] = "构建已取消"
            st["cancel_requested"] = False
            return BuildService.get_status(project_id)
        return None

    @staticmethod
    def cancel_build(project_id: str) -> dict:
        st = BuildService._state(project_id)
        st["cancel_requested"] = True
        st["status"] = "cancelled"
        st["message"] = "构建已取消"
        return BuildService.get_status(project_id)

    @staticmethod
    def start_async_build(project_id: str) -> dict:
        with _async_builds_lock:
            if project_id in _async_builds and not _async_builds[project_id].get("done"):
                return {"status": "already_running", "message": "构建已在运行"}
            st = BuildService._state(project_id)
            st["status"] = "starting"
            st["message"] = "正在启动构建..."
            st["cancel_requested"] = False
            _async_builds[project_id] = {"done": False, "result": None}
        thread = threading.Thread(target=_build_running_in_thread, args=(project_id,), daemon=True)
        thread.start()
        return {"status": "started", "message": "构建已启动"}

    @staticmethod
    def get_async_build_result(project_id: str) -> dict:
        with _async_builds_lock:
            build = _async_builds.get(project_id)
            if not build:
                return BuildService.get_status(project_id)
            if build.get("done"):
                return build["result"]
            return BuildService.get_status(project_id)

    @staticmethod
    def get_status(project_id: str) -> dict:
        st = BuildService._state(project_id)
        return {
            "status": st.get("status", "idle"),
            "message": st.get("message", ""),
            "artifact_version": st.get("artifact_version"),
            "runtime_status": st.get("runtime_status"),
            "preview_url": st.get("preview_url"),
        }

    @staticmethod
    def list_artifacts(project_id: str) -> list[dict]:
        artifacts_dir = BASE_DIR / "projects" / project_id / "artifacts"
        if not artifacts_dir.exists():
            return []
        artifacts = []
        for version_dir in sorted(artifacts_dir.iterdir()):
            if version_dir.is_dir():
                mf = version_dir / "manifest.json"
                if mf.exists():
                    with open(mf) as f:
                        m = json.load(f)
                    artifacts.append({
                        "version": version_dir.name,
                        "created_at": m.get("created_at", ""),
                        "path": str(version_dir),
                    })
        return artifacts
