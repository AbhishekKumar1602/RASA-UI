from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Project, Version, VersionLanguage
from app.services.promotion_helpers import (
    delete_version_data,
    clone_version_data,
    increment_version_label,
)
from app.services.guard_service import validate_all_intents_for_version


def promote_draft_to_production(
    db: Session,
    project_code: str,
):

    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(404, "Project not found")

    draft = (
        db.query(Version)
        .filter(
            Version.project_id == project.id,
            Version.status == "draft",
        )
        .first()
    )
    if not draft:
        raise HTTPException(400, "Draft version not found")

    production = (
        db.query(Version)
        .filter(
            Version.project_id == project.id,
            Version.status == "locked",
        )
        .first()
    )
    if not production:
        raise HTTPException(500, "Production version missing")

    if not (
        db.query(VersionLanguage).filter(VersionLanguage.version_id == draft.id).count()
    ):
        raise HTTPException(
            400,
            "Cannot promote without at least one enabled language",
        )

    validate_all_intents_for_version(db, draft.id)

    draft_version_label = draft.version_label
    new_draft_version_label = increment_version_label(draft_version_label)

    existing_archive = (
        db.query(Version)
        .filter(
            Version.project_id == project.id,
            Version.status == "archived",
        )
        .first()
    )
    if existing_archive:
        delete_version_data(db, existing_archive.id)
        db.delete(existing_archive)
        db.flush()

    archive = Version(
        project_id=project.id,
        version_label=production.version_label,
        status="archived",
    )
    db.add(archive)
    db.flush()

    clone_version_data(db, production.id, archive.id)

    delete_version_data(db, production.id)
    clone_version_data(db, draft.id, production.id)

    production.version_label = draft_version_label

    delete_version_data(db, draft.id)
    db.delete(draft)
    db.flush()

    new_draft = Version(
        project_id=project.id,
        version_label=new_draft_version_label,
        status="draft",
        parent_version_id=production.id,
    )
    db.add(new_draft)
    db.flush()

    clone_version_data(db, production.id, new_draft.id)

    db.commit()

    return {
        "message": "Promotion successful",
        "production_version": production.version_label,
        "new_draft_version": new_draft.version_label,
    }
