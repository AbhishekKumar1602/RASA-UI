from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Project, Version


def create_project(db: Session, project_code: str, project_name: str):
    """Create a new project with initial draft and production versions."""
    existing = db.query(Project).filter(Project.project_code == project_code).first()
    if existing:
        raise HTTPException(400, "Project with this project_code already exists")

    project = Project(
        project_code=project_code,
        project_name=project_name,
    )
    db.add(project)
    db.flush()

    draft_version = Version(
        project_id=project.id,
        version_label="v1",
        status="draft",
    )

    production_version = Version(
        project_id=project.id,
        version_label="v0",
        status="locked",
    )

    db.add_all([draft_version, production_version])
    db.commit()
    db.refresh(project)

    return project


def list_projects(db: Session):
    """List all projects."""
    return db.query(Project).order_by(Project.created_at.desc()).all()
