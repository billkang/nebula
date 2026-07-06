from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.project import Project
from app.models.user import User
from app.schemas.project import ProjectCreate, ProjectResponse


class ProjectService:
    @staticmethod
    def list_projects(db: Session, user: User) -> list[ProjectResponse]:
        projects = db.query(Project).filter(Project.owner_id == user.id
            ).order_by(Project.created_at.desc()).all()
        return [ProjectResponse(
            id=p.id, name=p.name, description=p.description,
            created_at=p.created_at.isoformat(), updated_at=p.updated_at.isoformat(),
        ) for p in projects]

    @staticmethod
    def create_project(req: ProjectCreate, db: Session, user: User) -> ProjectResponse:
        project = Project(name=req.name, description=req.description, owner_id=user.id)
        db.add(project)
        db.commit()
        db.refresh(project)
        return ProjectResponse(
            id=project.id, name=project.name, description=project.description,
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
            created_at=project.created_at.isoformat(), updated_at=project.updated_at.isoformat(),
        )

    @staticmethod
    def delete_project(project_id: str, db: Session):
        project = db.query(Project).filter(Project.id == project_id).first()
        if not project:
            raise HTTPException(status_code=404, detail="项目不存在")
        db.delete(project)
        db.commit()
