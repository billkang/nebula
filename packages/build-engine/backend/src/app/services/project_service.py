import logging
import shutil
import subprocess
from pathlib import Path

from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse
from app.llm import translate_change_name
from app.core.logging import biz_stage_start, biz_stage_end, biz_step, setup_project_logging

logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class ProjectService:
    @staticmethod
    def _project_dir(username: str, change_name: str) -> Path:
        return BASE_DIR / "projects" / f"{username}-{change_name}"

    @staticmethod
    def list_projects(db: Session, user: User) -> list[ProjectResponse]:
        projects = db.query(Project).filter(Project.owner_id == user.id
            ).order_by(Project.created_at.desc()).all()
        return [ProjectResponse(
            id=p.id, name=p.name, description=p.description,
            change_name=p.change_name,
            created_at=p.created_at.isoformat(), updated_at=p.updated_at.isoformat(),
        ) for p in projects]

    @staticmethod
    def create_project(req: ProjectCreate, db: Session, user: User) -> ProjectResponse:
        change_name: str | None = None
        biz_stage_start("CREATE_PROJECT", project_name=req.name, username=user.username)

        # 翻译项目名为 kebab-case change_name
        try:
            change_name = translate_change_name(req.name)
            biz_step("CREATE_PROJECT", "translate-name", name=req.name, result=change_name)
        except ValueError as e:
            logger.error("Failed to translate project name '%s': %s", req.name, e)
            biz_stage_end("CREATE_PROJECT", status="failed", reason="translate_failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"项目名称翻译失败：{e}")

        project = Project(
            name=req.name,
            description=req.description,
            owner_id=user.id,
            change_name=change_name,
        )
        db.add(project)
        db.commit()
        db.refresh(project)
        biz_step("CREATE_PROJECT", "db-record", project_id=project.id, change_name=change_name)

        # 创建项目文件系统目录并初始化 openspec 工作区
        project_dir = ProjectService._project_dir(user.username, change_name)
        try:
            project_dir.mkdir(parents=True, exist_ok=False)
            biz_step("CREATE_PROJECT", "fs-init", dir=str(project_dir))

            subprocess.run(
                ["openspec", "init", "--tools", "none"],
                cwd=str(project_dir),
                capture_output=True, text=True, check=True,
            )
            biz_step("CREATE_PROJECT", "openspec-init")

            # Set up per-project logging
            setup_project_logging(project_dir=str(project_dir), change_name=change_name)

        except FileExistsError:
            # 目录已存在 — 回滚 DB 记录
            db.delete(project)
            db.commit()
            biz_stage_end("CREATE_PROJECT", status="failed", reason="dir_exists", dir=str(project_dir))
            raise HTTPException(status_code=400, detail=f"项目目录已存在：{project_dir}")
        except subprocess.CalledProcessError as e:
            db.delete(project)
            db.commit()
            shutil.rmtree(project_dir, ignore_errors=True)
            stderr = e.stderr.strip() if e.stderr else ""
            logger.error("openspec init failed for '%s': %s", project_dir, stderr)
            biz_stage_end("CREATE_PROJECT", status="failed", reason="openspec_init_failed")
            raise HTTPException(status_code=500, detail=f"项目 openspec 初始化失败：{stderr}")
        except OSError as e:
            db.delete(project)
            db.commit()
            logger.error("Failed to create project directory '%s': %s", project_dir, e)
            biz_stage_end("CREATE_PROJECT", status="failed", reason="mkdir_failed", error=str(e))
            raise HTTPException(status_code=500, detail=f"创建项目目录失败：{e}")

        biz_stage_end("CREATE_PROJECT", status="ok", project_id=project.id, change_name=change_name)
        return ProjectResponse(
            id=project.id, name=project.name, description=project.description,
            change_name=project.change_name,
            created_at=project.created_at.isoformat(), updated_at=project.updated_at.isoformat(),
        )

    @staticmethod
    def get_project(project_id: str, db: Session, user: User) -> ProjectResponse:
        project = db.query(Project).filter(
            Project.id == project_id, Project.owner_id == user.id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        return ProjectResponse(
            id=project.id, name=project.name, description=project.description,
            change_name=project.change_name,
            created_at=project.created_at.isoformat(), updated_at=project.updated_at.isoformat(),
        )

    @staticmethod
    def delete_project(project_id: str, db: Session):
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")

        # 清理文件系统目录（失败不阻塞 DB 删除）
        username = db.query(User).filter(User.id == project.owner_id).first().username
        project_dir = ProjectService._project_dir(username, project.change_name)
        if project_dir.exists():
            try:
                shutil.rmtree(project_dir)
            except OSError as e:
                logger.warning("删除项目目录失败（不阻塞）: %s — %s", project_dir, e)

        db.delete(project)
        db.commit()
