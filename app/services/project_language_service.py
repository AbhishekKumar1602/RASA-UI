from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Project, Language, ProjectLanguage


def add_language_to_project(
    db: Session,
    project_code: str,
    language_code: str,
    is_default: bool = False,
):
    """Add a language to a project."""
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(404, "Project not found")

    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )
    if not language:
        raise HTTPException(404, "Language not found")

    existing = (
        db.query(ProjectLanguage)
        .filter(
            ProjectLanguage.project_id == project.id,
            ProjectLanguage.language_id == language.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Language already added to project")

    # Enforce single default language per project
    if is_default:
        db.query(ProjectLanguage).filter(
            ProjectLanguage.project_id == project.id,
            ProjectLanguage.is_default == True,
        ).update({"is_default": False})

    pl = ProjectLanguage(
        project_id=project.id,
        language_id=language.id,
        is_default=is_default,
    )

    db.add(pl)
    db.commit()
    db.refresh(pl)
    return pl


def list_project_languages(db: Session, project_code: str):
    """List all languages for a project."""
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(404, "Project not found")

    return (
        db.query(ProjectLanguage, Language)
        .join(Language, ProjectLanguage.language_id == Language.id)
        .filter(ProjectLanguage.project_id == project.id)
        .order_by(
            ProjectLanguage.is_default.desc(),
            Language.language_name,
        )
        .all()
    )
