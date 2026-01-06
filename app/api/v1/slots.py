from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.slot import (
    SlotCreate,
    SlotResponse,
    SlotUpdate,
    SlotMappingCreate,
    SlotMappingResponse,
    SlotMappingUpdate,
)
from app.services.slot_service import (
    create_slot,
    list_slots,
    get_slot,
    update_slot,
    delete_slot,
)
from app.services.slot_mapping_service import (
    add_slot_mapping,
    list_slot_mappings,
    get_slot_mapping,
    update_slot_mapping,
    delete_slot_mapping,
)


router = APIRouter(prefix="/projects", tags=["Slots"])


# -------------------------------------------------
# SLOT CRUD
# -------------------------------------------------

@router.post(
    "/{project_code}/versions/draft/slots",
    response_model=SlotResponse,
    status_code=201,
)
def create_slot_endpoint(
    project_code: str,
    payload: SlotCreate,
    db: Session = Depends(get_db),
):
    """Create a new slot in the draft version."""
    return create_slot(db, project_code, payload)


@router.get(
    "/{project_code}/versions/{status}/slots",
    response_model=List[SlotResponse],
)
def list_slots_endpoint(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    """List all slots for a version."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return list_slots(db, project_code, status)


@router.get(
    "/{project_code}/versions/{status}/slots/{slot_name}",
    response_model=SlotResponse,
)
def get_slot_endpoint(
    project_code: str,
    status: str,
    slot_name: str,
    db: Session = Depends(get_db),
):
    """Get a specific slot."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_slot(db, project_code, status, slot_name)


@router.put(
    "/{project_code}/versions/draft/slots/{slot_name}",
    response_model=SlotResponse,
)
def update_slot_endpoint(
    project_code: str,
    slot_name: str,
    payload: SlotUpdate,
    db: Session = Depends(get_db),
):
    """Update a slot in the draft version."""
    return update_slot(db, project_code, slot_name, payload)


@router.delete(
    "/{project_code}/versions/draft/slots/{slot_name}",
    status_code=204,
)
def delete_slot_endpoint(
    project_code: str,
    slot_name: str,
    db: Session = Depends(get_db),
):
    """Delete a slot from the draft version."""
    delete_slot(db, project_code, slot_name)
    return None


# -------------------------------------------------
# SLOT MAPPING CRUD
# -------------------------------------------------

@router.post(
    "/{project_code}/versions/draft/slots/{slot_name}/mappings",
    response_model=SlotMappingResponse,
    status_code=201,
)
def create_slot_mapping_endpoint(
    project_code: str,
    slot_name: str,
    payload: SlotMappingCreate,
    db: Session = Depends(get_db),
):
    """Create a new slot mapping."""
    m = add_slot_mapping(db, project_code, slot_name, payload)
    return SlotMappingResponse(
        id=m.id,
        mapping_type=m.mapping_type,
        entity_key=m.entity.entity_key if m.entity else None,
        role=m.role,
        group=m.group,
        intent=m.intent,
        not_intent=m.not_intent,
        active_loop=m.active_loop,
        priority=m.priority,
    )


@router.get(
    "/{project_code}/versions/{status}/slots/{slot_name}/mappings",
    response_model=List[SlotMappingResponse],
)
def list_slot_mappings_endpoint(
    project_code: str,
    status: str,
    slot_name: str,
    db: Session = Depends(get_db),
):
    """List all mappings for a slot."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return list_slot_mappings(db, project_code, status, slot_name)


@router.get(
    "/{project_code}/versions/{status}/slots/{slot_name}/mappings/{mapping_id}",
    response_model=SlotMappingResponse,
)
def get_slot_mapping_endpoint(
    project_code: str,
    status: str,
    slot_name: str,
    mapping_id: str,
    db: Session = Depends(get_db),
):
    """Get a specific slot mapping."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_slot_mapping(db, project_code, status, slot_name, mapping_id)


@router.put(
    "/{project_code}/versions/draft/slots/{slot_name}/mappings/{mapping_id}",
    response_model=SlotMappingResponse,
)
def update_slot_mapping_endpoint(
    project_code: str,
    slot_name: str,
    mapping_id: str,
    payload: SlotMappingUpdate,
    db: Session = Depends(get_db),
):
    """Update a slot mapping."""
    return update_slot_mapping(db, project_code, slot_name, mapping_id, payload)


@router.delete(
    "/{project_code}/versions/draft/slots/{slot_name}/mappings/{mapping_id}",
    status_code=204,
)
def delete_slot_mapping_endpoint(
    project_code: str,
    slot_name: str,
    mapping_id: str,
    db: Session = Depends(get_db),
):
    """Delete a slot mapping."""
    delete_slot_mapping(db, project_code, slot_name, mapping_id)
    return None







