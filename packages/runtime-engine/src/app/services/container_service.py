import time
import logging
from pathlib import Path
from typing import Optional

import docker
from docker.errors import DockerException, ImageNotFound, APIError

logger = logging.getLogger(__name__)

CONTAINER_LABEL = "nebula-managed"
DEFAULT_CPUS = 1.0
DEFAULT_MEMORY = "512m"
HEALTH_CHECK_TIMEOUT_S = 30
HEALTH_CHECK_INTERVAL_S = 2


class ContainerError(Exception):
    pass


class ContainerService:
    _client: Optional[docker.DockerClient] = None
    _current_container_id: Optional[str] = None
    _current_project_id: Optional[str] = None
    _current_version: Optional[str] = None
    _app_port: Optional[int] = None

    @classmethod
    def _get_client(cls) -> docker.DockerClient:
        if cls._client is None:
            try:
                cls._client = docker.from_env()
                cls._client.ping()
            except DockerException as e:
                raise ContainerError(f"Docker daemon not available: {e}")
        return cls._client

    @classmethod
    def check_prerequisites(cls) -> tuple[bool, str]:
        """Check Docker daemon availability."""
        try:
            client = cls._get_client()
            return True, f"Docker {client.version()['Version']} available"
        except (DockerException, ContainerError) as e:
            return False, str(e)

    @classmethod
    def start(cls, artifact_dir: Path, project_id: str, version: str) -> dict:
        """Build Docker image from artifact and start container."""
        client = cls._get_client()

        # Stop any existing container first
        if cls._current_container_id:
            cls._stop_container(cls._current_container_id)
            cls._current_container_id = None

        image_tag = f"nebula-app-{project_id}:{version}"
        container_name = f"nebula-app-{project_id}"

        # Build image from artifact's Dockerfile
        logger.info(f"Building Docker image {image_tag} from {artifact_dir}")
        try:
            image, build_logs = client.images.build(
                path=str(artifact_dir),
                tag=image_tag,
                dockerfile="Dockerfile",
                rm=True,
            )
            for log in build_logs:
                if "error" in log or "Error" in str(log):
                    logger.warning(f"Build log: {log}")
        except DockerException as e:
            error_msg = str(e)
            raise ContainerError(f"Docker build failed: {error_msg}")

        # Find an available port on the host
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", 0))
            host_port = s.getsockname()[1]

        # Run container
        try:
            container = client.containers.run(
                image_tag,
                name=container_name,
                detach=True,
                ports={"8000/tcp": host_port},
                mem_limit=DEFAULT_MEMORY,
                nano_cpus=int(DEFAULT_CPUS * 1e9),
                labels={CONTAINER_LABEL: "true"},
                remove=True,
            )
        except APIError as e:
            raise ContainerError(f"Failed to start container: {e}")

        cls._current_container_id = container.id
        cls._current_project_id = project_id
        cls._current_version = version
        cls._app_port = host_port

        # Wait for health check
        url = f"http://localhost:{host_port}/health"
        healthy = cls._wait_for_health(url)

        status_text = "running" if healthy else "degraded"
        return {
            "status": status_text,
            "url": f"http://localhost:{host_port}",
            "container_id": container.id,
            "project_id": project_id,
            "version": version,
            "health_checked": healthy,
        }

    @classmethod
    def stop(cls) -> dict:
        """Stop the currently running container."""
        if not cls._current_container_id:
            return {"status": "idle", "message": "No running container"}
        cls._stop_container(cls._current_container_id)
        cls._current_container_id = None
        cls._current_project_id = None
        cls._current_version = None
        cls._app_port = None
        return {"status": "stopped"}

    @classmethod
    def _stop_container(cls, container_id: str):
        try:
            client = cls._get_client()
            container = client.containers.get(container_id)
            container.stop(timeout=10)
        except docker.errors.NotFound:
            pass
        except DockerException as e:
            logger.warning(f"Error stopping container {container_id}: {e}")

    @classmethod
    def status(cls) -> dict:
        """Query current running status."""
        if not cls._current_container_id:
            return {"status": "idle"}

        try:
            client = cls._get_client()
            container = client.containers.get(cls._current_container_id)
            container_state = container.attrs.get("State", {})
            docker_status = container_state.get("Status", "unknown")

            return {
                "status": "running" if docker_status == "running" else docker_status,
                "project_id": cls._current_project_id,
                "version": cls._current_version,
                "container_id": cls._current_container_id,
                "url": f"http://localhost:{cls._app_port}",
                "started_at": container_state.get("StartedAt", ""),
            }
        except docker.errors.NotFound:
            cls._current_container_id = None
            return {"status": "idle"}
        except DockerException as e:
            return {"status": "error", "message": str(e)}

    @classmethod
    def logs(cls, tail: int = 100) -> str:
        """Get recent logs from the running container."""
        if not cls._current_container_id:
            return ""

        try:
            client = cls._get_client()
            container = client.containers.get(cls._current_container_id)
            log_output = container.logs(tail=tail, timestamps=True).decode("utf-8", errors="replace")
            return log_output
        except docker.errors.NotFound:
            return ""
        except DockerException as e:
            return f"Error fetching logs: {e}"

    @classmethod
    def _wait_for_health(cls, url: str) -> bool:
        """Wait for the application's health endpoint to respond successfully."""
        import requests
        deadline = time.time() + HEALTH_CHECK_TIMEOUT_S
        while time.time() < deadline:
            try:
                resp = requests.get(url, timeout=5)
                if resp.status_code == 200:
                    return True
            except (requests.ConnectionError, requests.Timeout):
                pass
            time.sleep(HEALTH_CHECK_INTERVAL_S)
        return False
