from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models import Form, Slot, FormSlotMapping
from app.models.form import FormRequiredSlot
from app.services.common import get_version_by_status, get_draft_version


def add_required_slot(db: Session, project_code: str, form_name: str, payload):
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

    slot = (
        db.query(Slot)
        .filter(
            Slot.version_id == version.id,
            Slot.name == payload.slot_name,
        )
        .first()
    )
    if not slot:
        raise HTTPException(404, "Slot not found in this version")

    exists = (
        db.query(FormRequiredSlot)
        .filter(
            FormRequiredSlot.form_id == form.id,
            FormRequiredSlot.slot_id == slot.id,
        )
        .first()
    )
    if exists:
        raise HTTPException(400, "Slot already added to this form")

    max_order = (
        db.query(FormRequiredSlot.order)
        .filter(FormRequiredSlot.form_id == form.id)
        .order_by(FormRequiredSlot.order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order else 1
    order = payload.order or next_order

    db.query(FormRequiredSlot).filter(
        FormRequiredSlot.form_id == form.id,
        FormRequiredSlot.order >= order,
    ).update(
        {FormRequiredSlot.order: FormRequiredSlot.order + 1},
        synchronize_session=False,
    )

    required_slot = FormRequiredSlot(
        form_id=form.id,
        slot_id=slot.id,
        order=order,
        required=payload.required,
    )

    db.add(required_slot)
    db.commit()
    db.refresh(required_slot)

    return required_slot


def list_required_slots(db: Session, project_code: str, status: str, form_name: str):
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

    slots = (
        db.query(FormRequiredSlot)
        .options(joinedload(FormRequiredSlot.slot))
        .filter(FormRequiredSlot.form_id == form.id)
        .order_by(FormRequiredSlot.order)
        .all()
    )

    return [
        {
            "id": frs.id,
            "slot_name": frs.slot.name,
            "order": frs.order,
            "required": frs.required,
        }
        for frs in slots
    ]


def update_required_slot(
    db: Session, project_code: str, form_name: str, slot_name: str, payload
):
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

    slot = (
        db.query(Slot)
        .filter(
            Slot.version_id == version.id,
            Slot.name == slot_name,
        )
        .first()
    )
    if not slot:
        raise HTTPException(404, "Slot not found")

    frs = (
        db.query(FormRequiredSlot)
        .filter(
            FormRequiredSlot.form_id == form.id,
            FormRequiredSlot.slot_id == slot.id,
        )
        .first()
    )
    if not frs:
        raise HTTPException(404, "Slot not part of this form")

    if payload.order is not None:
        frs.order = payload.order
    if payload.required is not None:
        frs.required = payload.required

    db.commit()
    db.refresh(frs)

    return {
        "id": frs.id,
        "slot_name": slot.name,
        "order": frs.order,
        "required": frs.required,
    }


def remove_required_slot(
    db: Session, project_code: str, form_name: str, slot_name: str
):
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

    slot = (
        db.query(Slot)
        .filter(
            Slot.version_id == version.id,
            Slot.name == slot_name,
        )
        .first()
    )
    if not slot:
        raise HTTPException(404, "Slot not found")

    frs = (
        db.query(FormRequiredSlot)
        .filter(
            FormRequiredSlot.form_id == form.id,
            FormRequiredSlot.slot_id == slot.id,
        )
        .first()
    )
    if not frs:
        raise HTTPException(404, "Slot not part of this form")

    removed_order = frs.order

    db.query(FormSlotMapping).filter(
        FormSlotMapping.form_required_slot_id == frs.id
    ).delete()

    db.delete(frs)

    db.query(FormRequiredSlot).filter(
        FormRequiredSlot.form_id == form.id,
        FormRequiredSlot.order > removed_order,
    ).update(
        {FormRequiredSlot.order: FormRequiredSlot.order - 1},
        synchronize_session=False,
    )

    db.commit()

    return {"message": "Slot removed from form"}
