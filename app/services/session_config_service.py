from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Project, Version, SessionConfig


def upsert_session_config(db: Session, project_code: str, payload):
    """Create or update session config for the draft version."""
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(404, "Project not found")

    version = (
        db.query(Version)
        .filter(
            Version.project_id == project.id,
            Version.status == "draft",
        )
        .first()
    )
    if not version:
        raise HTTPException(404, "Draft version not found")

    config = (
        db.query(SessionConfig).filter(SessionConfig.version_id == version.id).first()
    )

    if not config:
        config = SessionConfig(version_id=version.id)
        db.add(config)

    config.session_expiration_time = payload.session_expiration_time
    config.carry_over_slots_to_new_session = payload.carry_over_slots_to_new_session

    db.commit()
    db.refresh(config)

    return config
