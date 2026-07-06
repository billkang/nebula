import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from app.config import settings


REQUIRED_MANIFEST_FIELDS = ["version", "created_at", "entry"]
REQUIRED_ARTIFACT_ITEMS = ["src", "requirements.txt", "Dockerfile"]


class RegistryError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code


class RegistryService:

    @staticmethod
    def _artifacts_dir() -> Path:
        return Path(settings.artifacts_dir)

    @staticmethod
    def _project_dir(project_id: str) -> Path:
        p = RegistryService._artifacts_dir() / project_id
        p.mkdir(parents=True, exist_ok=True)
        return p

    @staticmethod
    def _version_dir(project_id: str, version: str) -> Path:
        return RegistryService._project_dir(project_id) / version

    @staticmethod
    def _next_version(project_id: str) -> str:
        """Auto-increment version based on existing version directories."""
        project_dir = RegistryService._project_dir(project_id)
        max_num = 0
        version_pattern = re.compile(r"^v(\d+)$")
        for item in project_dir.iterdir():
            if item.is_dir():
                m = version_pattern.match(item.name)
                if m:
                    num = int(m.group(1))
                    if num > max_num:
                        max_num = num
        return f"v{max_num + 1}"

    @staticmethod
    def list_versions(project_id: str) -> list[dict]:
        project_dir = RegistryService._project_dir(project_id)
        versions = []
        version_pattern = re.compile(r"^v(\d+)$")
        for item in sorted(project_dir.iterdir()):
            if item.is_dir() and version_pattern.match(item.name):
                mf = item / "manifest.json"
                metadata = {}
                if mf.exists():
                    with open(mf) as f:
                        metadata = json.load(f)
                versions.append({
                    "version": item.name,
                    "created_at": metadata.get("created_at", ""),
                    "status": metadata.get("status", "ready"),
                    "manifest": metadata,
                })
        return versions

    @staticmethod
    def get_version(project_id: str, version: str) -> dict:
        version_dir = RegistryService._version_dir(project_id, version)
        if not version_dir.exists():
            raise RegistryError(f"Version '{version}' not found", 404)
        mf = version_dir / "manifest.json"
        metadata = {}
        if mf.exists():
            with open(mf) as f:
                metadata = json.load(f)
        return {
            "version": version,
            "created_at": metadata.get("created_at", ""),
            "status": metadata.get("status", "ready"),
            "path": str(version_dir),
            "manifest": metadata,
        }

    @staticmethod
    def register_artifact(project_id: str, source_dir: str) -> dict:
        """Register a new artifact version from a source directory.

        Copies the source files into the registry and creates a manifest.
        """
        source = Path(source_dir)
        if not source.exists():
            raise RegistryError(f"Source directory not found: {source_dir}")

        version = RegistryService._next_version(project_id)
        version_dir = RegistryService._version_dir(project_id, version)
        version_dir.mkdir(parents=True, exist_ok=True)

        # Copy src/
        src_source = source / "src"
        src_dest = version_dir / "src"
        if src_source.exists():
            import shutil
            if src_dest.exists():
                shutil.rmtree(src_dest)
            shutil.copytree(src_source, src_dest)

        # Copy requirements.txt
        req_source = source / "requirements.txt"
        if req_source.exists():
            import shutil
            shutil.copy2(req_source, version_dir / "requirements.txt")

        # Copy Dockerfile
        df_source = source / "Dockerfile"
        if df_source.exists():
            import shutil
            shutil.copy2(df_source, version_dir / "Dockerfile")

        # Validate required items
        missing = RegistryService.verify_integrity(version_dir)
        if missing:
            import shutil
            shutil.rmtree(version_dir)
            raise RegistryError(f"Missing required items: {', '.join(missing)}")

        # Create manifest
        manifest = {
            "version": version,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "ready",
            "entry": "src/main.py",
            "dependencies": [],
        }
        req_file = version_dir / "requirements.txt"
        if req_file.exists():
            with open(req_file) as f:
                manifest["dependencies"] = [
                    line.strip() for line in f
                    if line.strip() and not line.startswith("#")
                ]

        manifest_path = version_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)

        return {"version": version, "status": "ready", "manifest": manifest}

    @staticmethod
    def delete_version(project_id: str, version: str) -> dict:
        version_dir = RegistryService._version_dir(project_id, version)
        if not version_dir.exists():
            raise RegistryError(f"Version '{version}' not found", 404)
        import shutil
        shutil.rmtree(version_dir)
        return {"status": "deleted", "version": version}

    @staticmethod
    def verify_integrity(artifact_dir: Path) -> list[str]:
        """Check that artifact has all required items. Returns list of missing items."""
        missing = []
        for item in REQUIRED_ARTIFACT_ITEMS:
            if not (artifact_dir / item).exists():
                missing.append(item)
        return missing

    @staticmethod
    def validate_manifest(manifest: dict) -> list[str]:
        """Validate manifest has all required fields. Returns list of missing fields."""
        missing = []
        for field in REQUIRED_MANIFEST_FIELDS:
            if field not in manifest:
                missing.append(field)
        return missing

    @staticmethod
    def get_artifact_path(project_id: str, version: str) -> Optional[Path]:
        version_dir = RegistryService._version_dir(project_id, version)
        if not version_dir.exists():
            return None
        return version_dir
