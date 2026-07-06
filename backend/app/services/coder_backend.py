from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional


@dataclass
class CodingResult:
    status: str  # "success" | "failed" | "cancelled" | "timeout"
    source_dir: str
    message: str
    error: Optional[str] = None


@dataclass
class BuildResult:
    status: str  # "success" | "failed" | "cancelled" | "timeout"
    message: str = ""
    artifact_path: Optional[str] = None
    version: Optional[str] = None
    test_output: Optional[str] = None
    error: Optional[str] = None


class CoderBackend(ABC):
    """Abstract base for coding execution backends."""

    @abstractmethod
    def execute_coding(
        self,
        spec: dict,
        skill: Any,
        project_dir: str,
        *,
        timeout: int = 3600,
    ) -> CodingResult:
        ...

    @abstractmethod
    def execute_build(
        self,
        project_dir: str,
        version: Optional[str] = None,
        *,
        timeout: int = 600,
    ) -> BuildResult:
        ...

    def cancel(self) -> None:
        pass
