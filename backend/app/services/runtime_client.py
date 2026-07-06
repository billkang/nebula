import json
import tarfile
import tempfile
from pathlib import Path
from typing import Optional

import httpx

from app.config import settings

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class RuntimeClientError(Exception):
    pass


class RuntimeClient:

    @staticmethod
    def runtime_url() -> str:
        return settings.runtime_url.rstrip("/")

    @staticmethod
    def is_available() -> bool:
        """Check if the runtime is reachable."""
        try:
            resp = httpx.get(f"{RuntimeClient.runtime_url()}/health", timeout=5)
            return resp.status_code == 200
        except (httpx.RequestError, httpx.TimeoutException):
            return False

    @staticmethod
    def push_artifact(project_id: str, version: str) -> dict:
        """Package an artifact from the platform's build output and push it to the runtime.

        Reads from projects/<project-id>/artifacts/<version>/ and sends it
        to the runtime's registry endpoint.
        """
        artifact_dir = BASE_DIR / "projects" / project_id / "artifacts" / version
        if not artifact_dir.exists():
            raise RuntimeClientError(f"Artifact directory not found: {artifact_dir}")

        # Create tar.gz in memory
        with tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False) as tmp:
            tar_path = tmp.name
        try:
            with tarfile.open(tar_path, "w:gz") as tar:
                src_dir = artifact_dir / "src"
                if src_dir.exists():
                    tar.add(str(src_dir), arcname="src")

                req_file = artifact_dir / "requirements.txt"
                if req_file.exists():
                    tar.add(str(req_file), arcname="requirements.txt")

                df_file = artifact_dir / "Dockerfile"
                if df_file.exists():
                    tar.add(str(df_file), arcname="Dockerfile")

                mf_file = artifact_dir / "manifest.json"
                if mf_file.exists():
                    tar.add(str(mf_file), arcname="manifest.json")

            # Upload to runtime
            url = f"{RuntimeClient.runtime_url()}/api/v1/registry/artifacts/{project_id}"
            with open(tar_path, "rb") as f:
                resp = httpx.post(url, files={"file": (f"artifact.tar.gz", f, "application/gzip")}, timeout=60)

            if resp.status_code >= 400:
                detail = resp.text
                try:
                    detail = resp.json().get("detail", detail)
                except (json.JSONDecodeError, KeyError):
                    pass
                raise RuntimeClientError(f"Runtime push failed ({resp.status_code}): {detail}")

            return resp.json().get("data", {})

        except httpx.RequestError as e:
            raise RuntimeClientError(f"Runtime unreachable: {e}")
        finally:
            Path(tar_path).unlink(missing_ok=True)

    @staticmethod
    def get_status(project_id: str, version: str) -> Optional[dict]:
        """Get the status of a specific artifact version on the runtime."""
        try:
            url = f"{RuntimeClient.runtime_url()}/api/v1/registry/artifacts/{project_id}/{version}"
            resp = httpx.get(url, timeout=10)
            if resp.status_code == 200:
                return resp.json().get("data", {})
            return None
        except httpx.RequestError:
            return None

    @staticmethod
    def start_application(project_id: str, version: str) -> dict:
        """Tell the runtime to start an application for the given artifact."""
        try:
            url = f"{RuntimeClient.runtime_url()}/api/v1/runtime/start"
            resp = httpx.post(url, json={"project_id": project_id, "version": version}, timeout=120)
            if resp.status_code >= 400:
                detail = resp.text
                try:
                    detail = resp.json().get("detail", detail)
                except (json.JSONDecodeError, KeyError):
                    pass
                raise RuntimeClientError(f"Runtime start failed ({resp.status_code}): {detail}")
            return resp.json().get("data", {})
        except httpx.RequestError as e:
            raise RuntimeClientError(f"Runtime unreachable: {e}")
