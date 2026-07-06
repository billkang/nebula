import subprocess, json, os, tarfile
from pathlib import Path
from datetime import datetime, timezone

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

# dict-based 状态存储，按 project_id 隔离
_build_states: dict[str, dict] = {}


class BuildService:

    @staticmethod
    def _state(project_id: str) -> dict:
        if project_id not in _build_states:
            _build_states[project_id] = {"status": "idle", "message": ""}
        return _build_states[project_id]

    @staticmethod
    def run_tests(project_dir: Path) -> tuple[bool, str]:
        result = subprocess.run(
            ["python", "-m", "pytest", "--tb=short", "-q"],
            capture_output=True, text=True, cwd=str(project_dir), timeout=300,
        )
        return result.returncode == 0, result.stdout + result.stderr

    @staticmethod
    def verify_integrity(project_dir: Path) -> list[str]:
        missing = []
        for item in ["src", "requirements.txt", "Dockerfile"]:
            if not (project_dir / item).exists():
                missing.append(item)
        return missing

    @staticmethod
    def package_artifact(project_dir: Path, version: str) -> tuple[str, dict]:
        artifact_dir = project_dir.parent / "artifacts" / version
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
    def build(project_id: str) -> dict:
        st = BuildService._state(project_id)
        project_dir = BASE_DIR / "projects" / project_id

        st["status"] = "testing"
        st["message"] = "正在运行测试..."
        passed, output = BuildService.run_tests(project_dir)
        if not passed:
            st["status"] = "failed"
            st["message"] = f"测试失败:\n{output[:500]}"
            return BuildService.get_status(project_id)

        st["status"] = "verifying"
        st["message"] = "正在验证完整性..."
        missing = BuildService.verify_integrity(project_dir)
        if missing:
            st["status"] = "failed"
            st["message"] = f"缺少必要文件: {', '.join(missing)}"
            return BuildService.get_status(project_id)

        st["status"] = "packaging"
        st["message"] = "正在打包 Artifact..."
        tar_path, manifest = BuildService.package_artifact(project_dir, "v1")

        st["status"] = "success"
        st["message"] = f"构建完成，Artifact: {tar_path}"
        return BuildService.get_status(project_id)

    @staticmethod
    def get_status(project_id: str) -> dict:
        st = BuildService._state(project_id)
        return {"status": st["status"], "message": st["message"]}

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
