from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Project, Version


def list_project_versions(db: Session, project_code: str):
    """List all versions for a project."""
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(404, "Project not found")

    return (
        db.query(Version)
        .filter(Version.project_id == project.id)
        .order_by(Version.created_at.desc())
        .all()
    )
