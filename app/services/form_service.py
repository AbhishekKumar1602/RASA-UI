from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Form, FormRequiredSlot, FormSlotMapping, Intent
from app.services.common import get_version_by_status, get_draft_version


def validate_ignored_intents(
    db: Session, version_id: str, ignored_intents: list[str] | None
):
    if not ignored_intents:
        return

    valid_intents = {
        i.intent_name
        for i in db.query(Intent).filter(Intent.version_id == version_id).all()
    }

    invalid = [intent for intent in ignored_intents if intent not in valid_intents]

    if invalid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid ignored intents for this version: {', '.join(invalid)}",
        )


def create_form(db: Session, project_code: str, payload):
    version = get_draft_version(db, project_code)

    existing = (
        db.query(Form)
        .filter(
            Form.version_id == version.id,
            Form.name == payload.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Form already exists in draft version")

    validate_ignored_intents(db, version.id, payload.ignored_intents)

    form = Form(
        name=payload.name,
        version_id=version.id,
        ignored_intents=payload.ignored_intents,
    )

    db.add(form)
    db.commit()
    db.refresh(form)

    return form


def list_forms(db: Session, project_code: str, status: str):
    version = get_version_by_status(db, project_code, status)

    return (
        db.query(Form).filter(Form.version_id == version.id).order_by(Form.name).all()
    )


def get_form(db: Session, project_code: str, status: str, form_name: str):
    version = get_version_by_status(db, project_code, status)

    form = (
        db.query(Form)
        .filter(
            Form.version_id == version.id,
            Form.name == form_name,
        )
        .first()
    )
    if not form:
        raise HTTPException(404, "Form not found")

    return form


def update_form(db: Session, project_code: str, form_name: str, payload):
    version = get_draft_version(db, project_code)

    form = (
        db.query(Form)
        .filter(
            Form.version_id == version.id,
            Form.name == form_name,
        )
        .first()
    )
    if not form:
        raise HTTPException(404, "Form not found")

    if payload.name and payload.name != form_name:
        existing = (
            db.query(Form)
            .filter(
                Form.version_id == version.id,
                Form.name == payload.name,
            )
            .first()
        )
        if existing:
            raise HTTPException(400, "Form with this name already exists")
        form.name = payload.name

    if payload.ignored_intents is not None:
        validate_ignored_intents(db, version.id, payload.ignored_intents)
        form.ignored_intents = payload.ignored_intents

    db.commit()
    db.refresh(form)
    return form


def delete_form(db: Session, project_code: str, form_name: str):
    version = get_draft_version(db, project_code)

    form = (
        db.query(Form)
        .filter(
            Form.version_id == version.id,
            Form.name == form_name,
        )
        .first()
    )
    if not form:
        raise HTTPException(404, "Form not found")

    required_slots = (
        db.query(FormRequiredSlot).filter(FormRequiredSlot.form_id == form.id).all()
    )
    for frs in required_slots:
        db.query(FormSlotMapping).filter(
            FormSlotMapping.form_required_slot_id == frs.id
        ).delete()

    db.query(FormRequiredSlot).filter(FormRequiredSlot.form_id == form.id).delete()

    db.delete(form)
    db.commit()
