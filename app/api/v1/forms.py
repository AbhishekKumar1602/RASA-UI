from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.form import (
    FormCreate,
    FormResponse,
    FormUpdate,
    FormSlotMappingCreate,
    FormSlotMappingResponse,
    FormRequiredSlotCreate,
    FormRequiredSlotResponse,
    FormRequiredSlotUpdate,
)
from app.services.form_service import (
    create_form,
    list_forms,
    get_form,
    update_form,
    delete_form,
)
from app.services.form_slot_mapping_service import (
    add_form_slot_mapping,
    list_form_slot_mappings,
    delete_form_slot_mapping,
)
from app.services.form_required_slot_service import (
    add_required_slot,
    list_required_slots,
    update_required_slot,
    remove_required_slot,
)


router = APIRouter(prefix="/projects", tags=["Forms"])


# -------------------------------------------------
# FORM CRUD
# -------------------------------------------------

@router.post(
    "/{project_code}/versions/draft/forms",
    response_model=FormResponse,
    status_code=201,
)
def create_form_endpoint(
    project_code: str,
    payload: FormCreate,
    db: Session = Depends(get_db),
):
    """Create a new form in the draft version."""
    return create_form(db, project_code, payload)


@router.get(
    "/{project_code}/versions/{status}/forms",
    response_model=List[FormResponse],
)
def list_forms_endpoint(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    """List all forms for a version."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return list_forms(db, project_code, status)


@router.get(
    "/{project_code}/versions/{status}/forms/{form_name}",
    response_model=FormResponse,
)
def get_form_endpoint(
    project_code: str,
    status: str,
    form_name: str,
    db: Session = Depends(get_db),
):
    """Get a specific form."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_form(db, project_code, status, form_name)


@router.put(
    "/{project_code}/versions/draft/forms/{form_name}",
    response_model=FormResponse,
)
def update_form_endpoint(
    project_code: str,
    form_name: str,
    payload: FormUpdate,
    db: Session = Depends(get_db),
):
    """Update a form in the draft version."""
    return update_form(db, project_code, form_name, payload)


@router.delete(
    "/{project_code}/versions/draft/forms/{form_name}",
    status_code=204,
)
def delete_form_endpoint(
    project_code: str,
    form_name: str,
    db: Session = Depends(get_db),
):
    """Delete a form from the draft version."""
    delete_form(db, project_code, form_name)
    return None


# -------------------------------------------------
# FORM REQUIRED SLOTS
# -------------------------------------------------

@router.post(
    "/{project_code}/versions/draft/forms/{form_name}/slots",
    response_model=FormRequiredSlotResponse,
    status_code=201,
)
def add_required_slot_endpoint(
    project_code: str,
    form_name: str,
    payload: FormRequiredSlotCreate,
    db: Session = Depends(get_db),
):
    """Add a required slot to a form."""
    frs = add_required_slot(db, project_code, form_name, payload)
    return FormRequiredSlotResponse(
        id=frs.id,
        slot_name=frs.slot.name,
        order=frs.order,
        required=frs.required,
    )


@router.get(
    "/{project_code}/versions/{status}/forms/{form_name}/slots",
    response_model=List[FormRequiredSlotResponse],
)
def list_required_slots_endpoint(
    project_code: str,
    status: str,
    form_name: str,
    db: Session = Depends(get_db),
):
    """List all required slots for a form."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return list_required_slots(db, project_code, status, form_name)


@router.put(
    "/{project_code}/versions/draft/forms/{form_name}/slots/{slot_name}",
    response_model=FormRequiredSlotResponse,
)
def update_required_slot_endpoint(
    project_code: str,
    form_name: str,
    slot_name: str,
    payload: FormRequiredSlotUpdate,
    db: Session = Depends(get_db),
):
    """Update a required slot's order or required flag."""
    return update_required_slot(db, project_code, form_name, slot_name, payload)


@router.delete(
    "/{project_code}/versions/draft/forms/{form_name}/slots/{slot_name}",
    status_code=204,
)
def remove_required_slot_endpoint(
    project_code: str,
    form_name: str,
    slot_name: str,
    db: Session = Depends(get_db),
):
    """Remove a required slot from a form."""
    remove_required_slot(db, project_code, form_name, slot_name)
    return None


# -------------------------------------------------
# FORM SLOT MAPPINGS
# -------------------------------------------------

@router.post(
    "/{project_code}/versions/draft/forms/{form_name}/slots/{slot_name}/mappings",
    response_model=FormSlotMappingResponse,
    status_code=201,
)
def add_form_slot_mapping_endpoint(
    project_code: str,
    form_name: str,
    slot_name: str,
    payload: FormSlotMappingCreate,
    db: Session = Depends(get_db),
):
    """Add a slot mapping to a form's required slot."""
    m = add_form_slot_mapping(db, project_code, form_name, slot_name, payload)
    return FormSlotMappingResponse(
        id=m.id,
        mapping_type=m.mapping_type,
        entity_key=m.entity.entity_key if m.entity else None,
        intent=m.intent,
        not_intent=m.not_intent,
    )


@router.get(
    "/{project_code}/versions/{status}/forms/{form_name}/slots/{slot_name}/mappings",
    response_model=List[FormSlotMappingResponse],
)
def list_form_slot_mappings_endpoint(
    project_code: str,
    status: str,
    form_name: str,
    slot_name: str,
    db: Session = Depends(get_db),
):
    """List all slot mappings for a form's required slot."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return list_form_slot_mappings(db, project_code, status, form_name, slot_name)


@router.delete(
    "/{project_code}/versions/draft/forms/{form_name}/slots/{slot_name}/mappings/{mapping_id}",
    status_code=204,
)
def delete_form_slot_mapping_endpoint(
    project_code: str,
    form_name: str,
    slot_name: str,
    mapping_id: str,
    db: Session = Depends(get_db),
):
    """Delete a slot mapping from a form's required slot."""
    delete_form_slot_mapping(db, project_code, form_name, slot_name, mapping_id)
    return None

