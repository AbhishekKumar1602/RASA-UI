from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Project, Version
from app.services.promotion_helpers import (
    delete_version_data,
    clone_version_data,
)


def rollback_production(
    db: Session,
    project_code: str,
):

    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(404, "Project not found")

    production = (
        db.query(Version)
        .filter(
            Version.project_id == project.id,
            Version.status == "locked",
        )
        .first()
    )

    archive = (
        db.query(Version)
        .filter(
            Version.project_id == project.id,
            Version.status == "archived",
        )
        .first()
    )

    if not production or not archive:
        raise HTTPException(
            400,
            "No archived version available for rollback",
        )

    delete_version_data(db, production.id)
    clone_version_data(db, archive.id, production.id)

    production.version_label = archive.version_label
    production.status = "locked"

    delete_version_data(db, archive.id)
    db.delete(archive)

    db.commit()

    return {
        "message": "Rollback successful",
        "production_version": production.version_label,
    }
