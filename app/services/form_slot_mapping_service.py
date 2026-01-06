from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models import Form, Slot, Entity, Intent
from app.models.form import FormSlotMapping, FormRequiredSlot
from app.services.common import get_version_by_status, get_draft_version


def add_form_slot_mapping(
    db: Session,
    project_code: str,
    form_name: str,
    slot_name: str,
    payload,
):
    """
    Add a slot mapping to a form's required slot.

    Supports mapping types:
    - from_entity: Extract from entity
    - from_text: Use full message text
    - from_intent: Set value when intent matches
    - from_trigger_intent: Set value from triggering intent
    """
    version = get_draft_version(db, project_code)

    # Get form
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

    # Get slot
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

    # Get form required slot
    frs = (
        db.query(FormRequiredSlot)
        .filter(
            FormRequiredSlot.form_id == form.id,
            FormRequiredSlot.slot_id == slot.id,
        )
        .first()
    )
    if not frs:
        raise HTTPException(404, "Slot is not a required slot in this form")

    # Validate entity for from_entity mapping
    entity = None
    if payload.mapping_type == "from_entity":
        if not payload.entity_key:
            raise HTTPException(400, "entity_key is required for from_entity mapping")

        entity = (
            db.query(Entity)
            .filter(
                Entity.version_id == version.id,
                Entity.entity_key == payload.entity_key,
            )
            .first()
        )
        if not entity:
            raise HTTPException(404, "Entity not found")

    # Validate intent for from_intent / from_trigger_intent mapping
    if payload.mapping_type in ("from_intent", "from_trigger_intent"):
        if not payload.intent:
            raise HTTPException(400, "intent is required for this mapping type")

        intent = (
            db.query(Intent)
            .filter(
                Intent.version_id == version.id,
                Intent.intent_name == payload.intent,
            )
            .first()
        )
        if not intent:
            raise HTTPException(404, "Intent not found")

    mapping = FormSlotMapping(
        form_required_slot_id=frs.id,
        mapping_type=payload.mapping_type,
        entity_id=entity.id if entity else None,
        intent=payload.intent,
        not_intent=payload.not_intent,
        value=payload.value,
    )

    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    return mapping


def list_form_slot_mappings(
    db: Session,
    project_code: str,
    status: str,
    form_name: str,
    slot_name: str,
):
    """List all slot mappings for a form's required slot."""
    version = get_version_by_status(db, project_code, status)

    # Get form
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

    # Get slot
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

    # Get form required slot
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

    mappings = (
        db.query(FormSlotMapping)
        .options(joinedload(FormSlotMapping.entity))
        .filter(FormSlotMapping.form_required_slot_id == frs.id)
        .all()
    )

    return [
        {
            "id": m.id,
            "mapping_type": m.mapping_type,
            "entity_key": m.entity.entity_key if m.entity else None,
            "intent": m.intent,
            "not_intent": m.not_intent,
            "value": m.value,
        }
        for m in mappings
    ]


def get_form_slot_mapping(
    db: Session,
    project_code: str,
    status: str,
    form_name: str,
    slot_name: str,
    mapping_id: str,
):
    """Get a specific form slot mapping."""
    version = get_version_by_status(db, project_code, status)

    # Get form
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

    # Get slot
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

    # Get form required slot
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

    mapping = (
        db.query(FormSlotMapping)
        .options(joinedload(FormSlotMapping.entity))
        .filter(
            FormSlotMapping.id == mapping_id,
            FormSlotMapping.form_required_slot_id == frs.id,
        )
        .first()
    )
    if not mapping:
        raise HTTPException(404, "Mapping not found")

    return {
        "id": mapping.id,
        "mapping_type": mapping.mapping_type,
        "entity_key": mapping.entity.entity_key if mapping.entity else None,
        "intent": mapping.intent,
        "not_intent": mapping.not_intent,
        "value": mapping.value,
    }


def update_form_slot_mapping(
    db: Session,
    project_code: str,
    form_name: str,
    slot_name: str,
    mapping_id: str,
    payload,
):
    """Update a form slot mapping."""
    version = get_draft_version(db, project_code)

    # Get form
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

    # Get slot
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

    # Get form required slot
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

    mapping = (
        db.query(FormSlotMapping)
        .filter(
            FormSlotMapping.id == mapping_id,
            FormSlotMapping.form_required_slot_id == frs.id,
        )
        .first()
    )
    if not mapping:
        raise HTTPException(404, "Mapping not found")

    # Update fields
    if hasattr(payload, "mapping_type") and payload.mapping_type is not None:
        mapping.mapping_type = payload.mapping_type

    if hasattr(payload, "entity_key") and payload.entity_key is not None:
        if payload.entity_key:
            entity = (
                db.query(Entity)
                .filter(
                    Entity.version_id == version.id,
                    Entity.entity_key == payload.entity_key,
                )
                .first()
            )
            if not entity:
                raise HTTPException(404, "Entity not found")
            mapping.entity_id = entity.id
        else:
            mapping.entity_id = None

    if hasattr(payload, "intent") and payload.intent is not None:
        mapping.intent = payload.intent
    if hasattr(payload, "not_intent") and payload.not_intent is not None:
        mapping.not_intent = payload.not_intent
    if hasattr(payload, "value") and payload.value is not None:
        mapping.value = payload.value

    db.commit()
    db.refresh(mapping)

    return {
        "id": mapping.id,
        "mapping_type": mapping.mapping_type,
        "entity_key": mapping.entity.entity_key if mapping.entity else None,
        "intent": mapping.intent,
        "not_intent": mapping.not_intent,
        "value": mapping.value,
    }


def delete_form_slot_mapping(
    db: Session,
    project_code: str,
    form_name: str,
    slot_name: str,
    mapping_id: str,
):
    """Delete a form slot mapping."""
    version = get_draft_version(db, project_code)

    # Get form
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

    # Get slot
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

    # Get form required slot
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

    mapping = (
        db.query(FormSlotMapping)
        .filter(
            FormSlotMapping.id == mapping_id,
            FormSlotMapping.form_required_slot_id == frs.id,
        )
        .first()
    )
    if not mapping:
        raise HTTPException(404, "Mapping not found")

    db.delete(mapping)
    db.commit()
