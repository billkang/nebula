from typing import Optional

import docker

from app.services.coder_backend import CoderBackend
from app.services.backends import create_backend

_exec_states: dict[str, dict] = {}


class ExecutorService:
    def __init__(self, backend: Optional[CoderBackend] = None):
        self._backend = backend or create_backend()

    @staticmethod
    def _state(project_id: str) -> dict:
        if project_id not in _exec_states:
            _exec_states[project_id] = {"status": "idle", "message": None}
        return _exec_states[project_id]

    @staticmethod
    def check_prerequisites() -> tuple[bool, str]:
        try:
            client = docker.from_env()
            client.ping()
            return True, "Docker daemon is available"
        except Exception as e:
            return False, f"Docker daemon not available: {e}"

    @staticmethod
    def get_status(project_id: str) -> dict:
        st = ExecutorService._state(project_id)
        return {"status": st["status"], "message": st["message"]}

    def execute(self, project_id: str, project_dir: str) -> dict:
        st = ExecutorService._state(project_id)
        available, msg = ExecutorService.check_prerequisites()
        if not available:
            st["status"] = "failed"
            st["message"] = msg
            return ExecutorService.get_status(project_id)

        st["status"] = "running"
        st["message"] = "编码执行中（Docker 容器）..."

        try:
            result = self._backend.execute_coding(
                spec={},
                skill=None,
                project_dir=project_dir,
            )
            st["status"] = result.status
            st["message"] = result.message
            if result.error:
                st["message"] = f"{result.message}: {result.error[:300]}"
        except Exception as e:
            st["status"] = "failed"
            st["message"] = f"编码执行异常: {str(e)[:500]}"

        return ExecutorService.get_status(project_id)

    def cancel(self) -> None:
        self._backend.cancel()
