from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models import Project, Version


def get_project(db: Session, project_code: str) -> Project:
    """Get project by project_code."""
    project = (
        db.query(Project)
        .filter(Project.project_code == project_code)
        .first()
    )
    if not project:
        raise HTTPException(404, "Project not found")
    return project


def get_version_by_status(
    db: Session,
    project_code: str,
    status: str,
) -> Version:
    """Get version by project_code and status."""
    project = get_project(db, project_code)
    
    version = (
        db.query(Version)
        .filter(
            Version.project_id == project.id,
            Version.status == status,
        )
        .first()
    )
    if not version:
        raise HTTPException(404, f"Version with status '{status}' not found")
    
    return version


def get_draft_version(db: Session, project_code: str) -> Version:
    """Get draft version for a project."""
    return get_version_by_status(db, project_code, "draft")


def validate_status(status: str) -> None:
    """Validate version status."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
