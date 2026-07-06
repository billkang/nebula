import json
import logging
import os
import subprocess
from typing import Any, Optional

import docker
from docker.errors import DockerException

from app.config import settings
from app.services.coder_backend import CoderBackend, CodingResult, BuildResult
from app.services.backends import register_backend

logger = logging.getLogger(__name__)


class DockerCoderBackend(CoderBackend):
    """Docker-based implementation of CoderBackend."""

    def __init__(self) -> None:
        self.client = docker.from_env()
        self._current_container_id: Optional[str] = None

    def execute_coding(
        self,
        spec: dict,
        skill: Any,
        project_dir: str,
        *,
        timeout: int = 3600,
    ) -> CodingResult:
        volumes = {project_dir: {"bind": "/workspace", "mode": "rw"}}

        environment = {"HOME": "/root"}
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if api_key:
            environment["ANTHROPIC_API_KEY"] = api_key

        try:
            container = self.client.containers.run(
                image=settings.coder_image,
                volumes=volumes,
                environment=environment,
                cpu_count=settings.coder_cpu_limit,
                mem_limit=settings.coder_memory_limit,
                detach=True,
                tty=True,
            )
        except DockerException as e:
            logger.error("Failed to start coding container: %s", e)
            return CodingResult(
                status="failed",
                source_dir=str(project_dir),
                message="Failed to start coding container",
                error=str(e),
            )

        self._current_container_id = container.id
        prompt_text = self._build_coding_prompt(spec, skill)

        try:
            exit_code, output = container.exec_run(
                cmd=["claude", "code", "--prompt", prompt_text, "--print"],
                workdir="/workspace",
                timeout=timeout,
            )
        except Exception as e:
            self._cleanup_container(container.id)
            logger.warning("Coding execution failed: %s", e)
            return CodingResult(
                status="failed",
                source_dir=str(project_dir),
                message="Coding execution failed",
                error=str(e),
            )

        self._cleanup_container(container.id)
        output_text = output.decode("utf-8", errors="replace") if isinstance(output, bytes) else str(output)

        if exit_code == 0:
            self._fix_permissions(project_dir)
            return CodingResult(
                status="success",
                source_dir=str(project_dir),
                message="Coding completed",
            )
        else:
            return CodingResult(
                status="failed",
                source_dir=str(project_dir),
                message="Coding execution failed",
                error=output_text[:2000],
            )

    def execute_build(
        self,
        project_dir: str,
        version: Optional[str] = None,
        *,
        timeout: int = 600,
    ) -> BuildResult:
        volumes = {project_dir: {"bind": "/workspace", "mode": "rw"}}
        # Ensure artifacts directory exists on host before container starts
        os.makedirs(f"{project_dir}/artifacts", exist_ok=True)

        environment = {}
        if version:
            environment["VERSION"] = version

        try:
            output = self.client.containers.run(
                image=settings.builder_image,
                volumes=volumes,
                environment=environment,
                cpu_count=settings.builder_cpu_limit,
                mem_limit=settings.builder_memory_limit,
                # Security: builder needs outbound network for `pip install -r requirements.txt`
                # from PyPI. For stricter isolation, use private PyPI mirror or pre-install all
                # dependencies in the builder image.
                detach=False,
                remove=True,
            )
            exit_code = 0
        except DockerException as e:
            logger.error("Build container failed: %s", e)
            return BuildResult(
                status="failed",
                message="Build container failed",
                error=str(e),
            )

        output_text = output.decode("utf-8", errors="replace") if isinstance(output, bytes) else str(output)

        if exit_code == 0:
            self._fix_permissions(f"{project_dir}/artifacts")
            return BuildResult(
                status="success",
                artifact_path=f"{project_dir}/artifacts/artifact.tar.gz",
                version=version,
                test_output=output_text[:2000],
                message="Build completed",
            )
        else:
            return BuildResult(
                status="failed",
                message="Build failed",
                test_output=output_text[:2000],
                error=output_text[:2000],
            )

    def cancel(self) -> None:
        if self._current_container_id:
            try:
                container = self.client.containers.get(self._current_container_id)
                container.stop(timeout=10)
                container.remove()
            except Exception as e:
                logger.warning("Error cancelling container %s: %s", self._current_container_id, e)
            self._current_container_id = None

    def _cleanup_container(self, container_id: str) -> None:
        try:
            container = self.client.containers.get(container_id)
            container.stop(timeout=10)
            container.remove()
        except Exception as e:
            logger.warning("Error cleaning up container %s: %s", container_id, e)
        if self._current_container_id == container_id:
            self._current_container_id = None

    def _fix_permissions(self, path: str) -> None:
        uid = os.environ.get("HOST_UID", str(os.getuid()))
        gid = os.environ.get("HOST_GID", str(os.getgid()))
        try:
            subprocess.run(
                ["chown", "-R", f"{uid}:{gid}", path],
                capture_output=True,
                timeout=30,
            )
        except Exception as e:
            logger.warning("Error fixing permissions for %s: %s", path, e)

    def _build_coding_prompt(self, spec: dict, skill: Any) -> str:
        if skill and hasattr(skill, "coding_prompt"):
            return skill.coding_prompt
        if spec:
            return (
                "请根据以下技术规格实现功能代码：\n\n"
                f"{json.dumps(spec, indent=2, ensure_ascii=False)}"
            )
        return "请实现功能代码。"


# Auto-register at import time
register_backend("docker", DockerCoderBackend)
