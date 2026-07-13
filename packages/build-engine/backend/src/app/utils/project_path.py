"""Utility for resolving project IDs to filesystem paths.

All project filesystem directories live under backend/{projects_dir}/{username}-{change_name}/.
This module centralizes path resolution so all services use the same convention.
"""

import os
from pathlib import Path
from sqlalchemy.orm import Session

from app.models.project import Project
from app.models.user import User
from app.config import settings

# Backend root directory (two levels up from app/utils/)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent.parent


def get_projects_base() -> Path:
    """Return the base projects directory, e.g. backend/projects/ or backend/projects_test/."""
    return BACKEND_DIR / settings.projects_dir


def resolve_project_dir(project_id: str, db: Session) -> str:
    """Resolve a project UUID to its canonical filesystem path.

    Returns: {projects_dir}/{username}-{change_name}/
    Raises ValueError if the project or its owner cannot be found.
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project or not project.change_name:
        raise ValueError(f"Project {project_id} not found or missing change_name")
    user = db.query(User).filter(User.id == project.owner_id).first()
    if not user:
        raise ValueError(f"Owner not found for project {project_id}")
    return str(get_projects_base() / f"{user.username}-{project.change_name}")


def ensure_project_dir(project_id: str, db: Session) -> str:
    """Resolve project directory and create it if missing.

    Returns the resolved directory path.
    """
    path = resolve_project_dir(project_id, db)
    os.makedirs(path, exist_ok=True)
    return path
