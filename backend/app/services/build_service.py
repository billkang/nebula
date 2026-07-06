import subprocess, json, os, tarfile, threading
from pathlib import Path
from datetime import datetime, timezone

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# dict-based 状态存储，按 project_id 隔离
_build_states: dict[str, dict] = {}

# 异步构建的线程和进程引用
_async_builds: dict[str, dict] = {}
_async_builds_lock = threading.Lock()


def _build_running_in_thread(project_id: str):
    """在后台线程中运行完整的构建流程。
    启动后，POST /rebuild 可以立即返回，前端通过 GET /rebuild/status 轮询进度。
    """
    try:
        result = BuildService.build(project_id)
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

    @staticmethod
    def _state(project_id: str) -> dict:
        if project_id not in _build_states:
            _build_states[project_id] = {"status": "idle", "message": ""}
        return _build_states[project_id]

    @staticmethod
    def run_tests(project_id: str, project_dir: Path) -> tuple[bool, str]:
        """运行测试，支持取消。使用 Popen 以便在取消时杀掉进程。"""
        proc = subprocess.Popen(
            ["python", "-m", "pytest", "--tb=short", "-q"],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, cwd=str(project_dir),
        )

        # 存储进程引用以便取消
        st = BuildService._state(project_id)
        st["async_process"] = proc

        try:
            stdout, _ = proc.communicate(timeout=300)
            return proc.returncode == 0, stdout or ""
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            return False, "测试超时 (300s)"
        finally:
            st["async_process"] = None

    @staticmethod
    def _check_cancelled(project_id: str) -> dict | None:
        """检查是否已取消；如果已取消则返回取消状态 dict，否则返回 None。"""
        st = BuildService._state(project_id)
        if st.get("cancel_requested"):
            st["status"] = "cancelled"
            st["message"] = "构建已取消"
            st["cancel_requested"] = False  # 清除标记
            return BuildService.get_status(project_id)
        return None

    @staticmethod
    def verify_integrity(project_dir: Path) -> list[str]:
        missing = []
        for item in ["src", "requirements.txt", "Dockerfile"]:
            if not (project_dir / item).exists():
                missing.append(item)
        return missing

    @staticmethod
    def package_artifact(project_dir: Path, version: str) -> tuple[str, dict]:
        artifact_dir = project_dir / "artifacts" / version
        artifact_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "entry": "src/main.py",
            "dependencies": [],
        }
        req_file = project_dir / "requirements.txt"
        if req_file.exists():
            with open(req_file) as f:
                manifest["dependencies"] = [
                    line.strip() for line in f
                    if line.strip() and not line.startswith("#")
                ]

        manifest_path = artifact_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        tar_path = artifact_dir / "artifact.tar.gz"
        with tarfile.open(tar_path, "w:gz") as tar:
            tar.add(project_dir / "src", arcname="src")
            tar.add(project_dir / "requirements.txt", arcname="requirements.txt")
            tar.add(project_dir / "Dockerfile", arcname="Dockerfile")
            tar.add(manifest_path, arcname="manifest.json")

        return str(tar_path), manifest

    @staticmethod
    def build(project_id: str, source_dir: str | None = None) -> dict:
        st = BuildService._state(project_id)
        project_dir = Path(source_dir) if source_dir else BASE_DIR / "projects" / project_id

        # ── 阶段 1: 测试 ──
        if BuildService._check_cancelled(project_id):
            return BuildService.get_status(project_id)
        st["status"] = "testing"
        st["message"] = "正在运行测试..."
        passed, output = BuildService.run_tests(project_id, project_dir)
        if st.get("cancel_requested"):
            st["status"] = "cancelled"
            st["message"] = "构建已取消（测试完成后终止）"
            st["cancel_requested"] = False
            return BuildService.get_status(project_id)
        if not passed:
            st["status"] = "failed"
            st["message"] = f"测试失败:\n{output[:500]}"
            return BuildService.get_status(project_id)

        # ── 阶段 2: 验证 ──
        if BuildService._check_cancelled(project_id):
            return BuildService.get_status(project_id)
        st["status"] = "verifying"
        st["message"] = "正在验证完整性..."
        missing = BuildService.verify_integrity(project_dir)
        if missing:
            st["status"] = "failed"
            st["message"] = f"缺少必要文件: {', '.join(missing)}"
            return BuildService.get_status(project_id)

        # ── 阶段 3: 打包 ──
        if BuildService._check_cancelled(project_id):
            return BuildService.get_status(project_id)
        st["status"] = "packaging"
        st["message"] = "正在打包 Artifact..."

        # 计算下一个版本号
        existing_versions = BuildService.list_artifacts(project_id)
        max_num = 0
        for v in existing_versions:
            vname = v["version"]
            if vname.startswith("v") and vname[1:].isdigit():
                num = int(vname[1:])
                if num > max_num:
                    max_num = num
        version = f"v{max_num + 1}"

        tar_path, manifest = BuildService.package_artifact(project_dir, version)

        # ── 阶段 4: 推送 ──
        if BuildService._check_cancelled(project_id):
            return BuildService.get_status(project_id)

        st["status"] = "success"
        st["message"] = f"构建完成，Artifact: {tar_path}"
        st["artifact_version"] = version

        # 尝试推送到 nebula-runtime（可选，不阻塞构建流程）
        try:
            from app.services.runtime_client import RuntimeClient
            if RuntimeClient.is_available():
                RuntimeClient.push_artifact(project_id, version)
                RuntimeClient.start_application(project_id, version)
                st["runtime_status"] = "pushed"
                st["preview_url"] = f"{settings.runtime_url}/preview/{project_id}"
            else:
                st["runtime_status"] = "runtime_unavailable"
        except Exception as e:
            st["runtime_status"] = f"push_failed: {str(e)[:200]}"

        return BuildService.get_status(project_id)

    @staticmethod
    def cancel_build(project_id: str) -> dict:
        """取消正在进行的构建。"""
        st = BuildService._state(project_id)
        st["cancel_requested"] = True

        # 如果有正在运行的测试进程，杀掉它
        proc = st.get("async_process")
        if proc and isinstance(proc, subprocess.Popen):
            try:
                proc.kill()
            except Exception:
                pass

        st["status"] = "cancelled"
        st["message"] = "构建已取消"
        return BuildService.get_status(project_id)

    @staticmethod
    def start_async_build(project_id: str) -> dict:
        """在后台线程启动异步构建。
        返回启动状态，前端通过 get_status / get_async_build_result 获取结果。
        """
        with _async_builds_lock:
            if project_id in _async_builds and not _async_builds[project_id].get("done"):
                return {"status": "already_running", "message": "构建已在运行"}

            st = BuildService._state(project_id)
            st["status"] = "starting"
            st["message"] = "正在启动构建..."
            st["cancel_requested"] = False
            st.pop("async_process", None)

            _async_builds[project_id] = {"done": False, "result": None}

        thread = threading.Thread(target=_build_running_in_thread, args=(project_id,), daemon=True)
        thread.start()
        return {"status": "started", "message": "构建已启动"}

    @staticmethod
    def get_async_build_result(project_id: str) -> dict:
        """获取异步构建结果。如果没有运行中的构建，返回 None。"""
        with _async_builds_lock:
            build = _async_builds.get(project_id)
            if not build:
                return BuildService.get_status(project_id)
            if build.get("done"):
                return build["result"]
            # 还在运行中，返回当前状态
            return BuildService.get_status(project_id)

    @staticmethod
    def get_status(project_id: str) -> dict:
        st = BuildService._state(project_id)
        # 返回完整状态（含 artifact_version、runtime_status、preview_url）
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
