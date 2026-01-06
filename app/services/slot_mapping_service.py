from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException
from app.models import Slot, SlotMapping, Entity, Intent
from app.services.common import get_version_by_status, get_draft_version


def add_slot_mapping(db: Session, project_code: str, slot_name: str, payload):
    """
    Add a mapping to a slot.

    Supports all RASA mapping types:
    - from_entity: Extract from entity
    - from_text: Use full message text
    - from_intent: Set value when intent matches
    - from_trigger_intent: Set value from triggering intent
    - custom: Custom action fills slot
    """
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

    # Handle conditions - convert legacy active_loop to conditions format
    conditions = payload.conditions
    if not conditions and payload.active_loop:
        # Legacy support: convert single active_loop to conditions array
        conditions = [{"active_loop": payload.active_loop}]

    mapping = SlotMapping(
        slot_id=slot.id,
        mapping_type=payload.mapping_type,
        entity_id=entity.id if entity else None,
        role=payload.role,
        group=payload.group,
        intent=payload.intent,
        not_intent=payload.not_intent,
        value=payload.value,
        conditions=conditions,
        active_loop=payload.active_loop,  # Keep for backward compatibility
        priority=payload.priority,
    )

    db.add(mapping)
    db.commit()
    db.refresh(mapping)

    return mapping


def list_slot_mappings(db: Session, project_code: str, status: str, slot_name: str):
    """List all mappings for a slot."""
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

    mappings = (
        db.query(SlotMapping)
        .options(joinedload(SlotMapping.entity))
        .filter(SlotMapping.slot_id == slot.id)
        .order_by(SlotMapping.priority.desc())
        .all()
    )

    return [
        {
            "id": m.id,
            "mapping_type": m.mapping_type,
            "entity_key": m.entity.entity_key if m.entity else None,
            "role": m.role,
            "group": m.group,
            "intent": m.intent,
            "not_intent": m.not_intent,
            "value": m.value,
            "conditions": m.conditions,
            "active_loop": m.active_loop,
            "priority": m.priority,
        }
        for m in mappings
    ]


def get_slot_mapping(
    db: Session, project_code: str, status: str, slot_name: str, mapping_id: str
):
    """Get a specific slot mapping."""
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

    mapping = (
        db.query(SlotMapping)
        .options(joinedload(SlotMapping.entity))
        .filter(
            SlotMapping.id == mapping_id,
            SlotMapping.slot_id == slot.id,
        )
        .first()
    )
    if not mapping:
        raise HTTPException(404, "Slot mapping not found")

    return {
        "id": mapping.id,
        "mapping_type": mapping.mapping_type,
        "entity_key": mapping.entity.entity_key if mapping.entity else None,
        "role": mapping.role,
        "group": mapping.group,
        "intent": mapping.intent,
        "not_intent": mapping.not_intent,
        "value": mapping.value,
        "conditions": mapping.conditions,
        "active_loop": mapping.active_loop,
        "priority": mapping.priority,
    }


def update_slot_mapping(
    db: Session, project_code: str, slot_name: str, mapping_id: str, payload
):
    """Update a slot mapping."""
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

    mapping = (
        db.query(SlotMapping)
        .filter(
            SlotMapping.id == mapping_id,
            SlotMapping.slot_id == slot.id,
        )
        .first()
    )
    if not mapping:
        raise HTTPException(404, "Slot mapping not found")

    # Update mapping type
    if payload.mapping_type is not None:
        mapping.mapping_type = payload.mapping_type

    # Update entity reference
    if payload.entity_key is not None:
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

    # Update other fields
    if payload.role is not None:
        mapping.role = payload.role
    if payload.group is not None:
        mapping.group = payload.group
    if payload.intent is not None:
        mapping.intent = payload.intent
    if payload.not_intent is not None:
        mapping.not_intent = payload.not_intent
    if payload.value is not None:
        mapping.value = payload.value
    if payload.conditions is not None:
        mapping.conditions = payload.conditions
    if payload.active_loop is not None:
        mapping.active_loop = payload.active_loop
    if payload.priority is not None:
        mapping.priority = payload.priority

    db.commit()
    db.refresh(mapping)

    return {
        "id": mapping.id,
        "mapping_type": mapping.mapping_type,
        "entity_key": mapping.entity.entity_key if mapping.entity else None,
        "role": mapping.role,
        "group": mapping.group,
        "intent": mapping.intent,
        "not_intent": mapping.not_intent,
        "value": mapping.value,
        "conditions": mapping.conditions,
        "active_loop": mapping.active_loop,
        "priority": mapping.priority,
    }


def delete_slot_mapping(
    db: Session, project_code: str, slot_name: str, mapping_id: str
):
    """Delete a slot mapping."""
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

    mapping = (
        db.query(SlotMapping)
        .filter(
            SlotMapping.id == mapping_id,
            SlotMapping.slot_id == slot.id,
        )
        .first()
    )
    if not mapping:
        raise HTTPException(404, "Slot mapping not found")

    db.delete(mapping)
    db.commit()
