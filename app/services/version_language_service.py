from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Project, Version, Language, ProjectLanguage, VersionLanguage


def add_language_to_draft_version(
    db: Session,
    project_code: str,
    language_code: str,
):
    """Add a language to the draft version."""
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(404, "Project not found")

    draft_version = (
        db.query(Version)
        .filter(
            Version.project_id == project.id,
            Version.status == "draft",
        )
        .first()
    )
    if not draft_version:
        raise HTTPException(404, "Draft version not found")

    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )
    if not language:
        raise HTTPException(404, "Language not found")

    # Ensure language is added to project
    project_language = (
        db.query(ProjectLanguage)
        .filter(
            ProjectLanguage.project_id == project.id,
            ProjectLanguage.language_id == language.id,
        )
        .first()
    )
    if not project_language:
        raise HTTPException(400, "Language not added to project")

    # Duplicate guard
    existing = (
        db.query(VersionLanguage)
        .filter(
            VersionLanguage.version_id == draft_version.id,
            VersionLanguage.language_id == language.id,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Language already added to draft version")

    vl = VersionLanguage(
        version_id=draft_version.id,
        language_id=language.id,
        is_default=False,
    )

    db.add(vl)
    db.commit()
    db.refresh(vl)

    return vl


def list_version_languages(db: Session, project_code: str, status: str):
    """List languages for a version."""
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(404, "Project not found")

    version = (
        db.query(Version)
        .filter(
            Version.project_id == project.id,
            Version.status == status,
        )
        .first()
    )
    if not version:
        raise HTTPException(404, "Version not found")

    return (
        db.query(VersionLanguage, Language)
        .join(Language, VersionLanguage.language_id == Language.id)
        .filter(VersionLanguage.version_id == version.id)
        .all()
    )
