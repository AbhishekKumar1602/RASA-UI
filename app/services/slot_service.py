from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Slot, SlotMapping
from app.services.common import get_version_by_status, get_draft_version


def validate_slot_payload(payload):
    if hasattr(payload, "slot_type") and payload.slot_type:
        if payload.slot_type == "categorical":
            if hasattr(payload, "values") and not payload.values:
                raise HTTPException(400, "Categorical slot requires non-empty values")

        if payload.slot_type == "float":
            min_val = getattr(payload, "min_value", None)
            max_val = getattr(payload, "max_value", None)
            if min_val is None or max_val is None:
                raise HTTPException(400, "Float slot requires min_value and max_value")
            if min_val >= max_val:
                raise HTTPException(400, "min_value must be less than max_value")

        if (
            payload.slot_type != "categorical"
            and hasattr(payload, "values")
            and payload.values is not None
        ):
            raise HTTPException(400, "Only categorical slots can have values")

        if payload.slot_type != "float":
            if (hasattr(payload, "min_value") and payload.min_value is not None) or (
                hasattr(payload, "max_value") and payload.max_value is not None
            ):
                raise HTTPException(400, "Only float slots can have min/max values")


def create_slot(db: Session, project_code: str, payload):
    version = get_draft_version(db, project_code)

    existing = (
        db.query(Slot)
        .filter(
            Slot.version_id == version.id,
            Slot.name == payload.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Slot already exists in this version")

    validate_slot_payload(payload)

    slot = Slot(
        name=payload.name,
        version_id=version.id,
        slot_type=payload.slot_type,
        influence_conversation=payload.influence_conversation,
        initial_value=payload.initial_value,
        values=payload.values,
        min_value=payload.min_value,
        max_value=payload.max_value,
    )

    db.add(slot)
    db.commit()
    db.refresh(slot)

    return slot


def list_slots(db: Session, project_code: str, status: str):
    version = get_version_by_status(db, project_code, status)

    return (
        db.query(Slot).filter(Slot.version_id == version.id).order_by(Slot.name).all()
    )


def get_slot(db: Session, project_code: str, status: str, slot_name: str):
    version = get_version_by_status(db, project_code, status)

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

    return slot


def update_slot(db: Session, project_code: str, slot_name: str, payload):
    version = get_draft_version(db, project_code)

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

    if payload.name and payload.name != slot_name:
        existing = (
            db.query(Slot)
            .filter(
                Slot.version_id == version.id,
                Slot.name == payload.name,
            )
            .first()
        )
        if existing:
            raise HTTPException(400, "Slot with this name already exists")
        slot.name = payload.name

    if payload.slot_type is not None:
        slot.slot_type = payload.slot_type
    if payload.influence_conversation is not None:
        slot.influence_conversation = payload.influence_conversation
    if payload.initial_value is not None:
        slot.initial_value = payload.initial_value
    if payload.values is not None:
        slot.values = payload.values
    if payload.min_value is not None:
        slot.min_value = payload.min_value
    if payload.max_value is not None:
        slot.max_value = payload.max_value

    validate_slot_payload(slot)

    db.commit()
    db.refresh(slot)
    return slot


def delete_slot(db: Session, project_code: str, slot_name: str):
    version = get_draft_version(db, project_code)

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

    db.query(SlotMapping).filter(SlotMapping.slot_id == slot.id).delete()

    db.delete(slot)
    db.commit()
