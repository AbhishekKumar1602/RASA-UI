from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.response import (
    ResponseCreate, ResponseUpdate, ResponseResponse, ResponseDetailResponse,
    ResponseVariantCreate, ResponseVariantResponse, ResponseUpsert
)
from app.services.response_service import (
    create_response,
    list_responses,
    get_response,
    update_response,
    delete_response,
    add_response_variant,
    list_response_variants,
    delete_response_variant,
    upsert_response_with_variants,
)


router = APIRouter(prefix="/projects", tags=["Responses"])


# ============================================================
# RESPONSE CRUD
# ============================================================

@router.post(
    "/{project_code}/versions/draft/responses",
    response_model=ResponseResponse,
    status_code=201,
)
def create_response_endpoint(
    project_code: str,
    payload: ResponseCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new response (utterance) in the draft version.
    
    Responses are bot messages that can include text, buttons, images, etc.
    The name must start with 'utter_' (e.g., utter_greet, utter_goodbye).
    
    NOTE: For custom actions (action_fetch_bill), use the /actions endpoint instead.
    """
    return create_response(db, project_code, payload)


@router.get(
    "/{project_code}/versions/{status}/responses",
    response_model=List[ResponseResponse],
)
def list_responses_endpoint(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    """List all responses for a version."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return list_responses(db, project_code, status)


@router.get(
    "/{project_code}/versions/{status}/responses/{response_name}",
    response_model=ResponseDetailResponse,
)
def get_response_endpoint(
    project_code: str,
    status: str,
    response_name: str,
    db: Session = Depends(get_db),
):
    """Get a specific response with all its variants."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_response(db, project_code, status, response_name)


@router.put(
    "/{project_code}/versions/draft/responses/{response_name}",
    response_model=ResponseResponse,
)
def update_response_endpoint(
    project_code: str,
    response_name: str,
    payload: ResponseUpdate,
    db: Session = Depends(get_db),
):
    """Update a response in the draft version."""
    return update_response(db, project_code, response_name, payload)


@router.delete(
    "/{project_code}/versions/draft/responses/{response_name}",
    status_code=204,
)
def delete_response_endpoint(
    project_code: str,
    response_name: str,
    db: Session = Depends(get_db),
):
    """Delete a response from the draft version."""
    delete_response(db, project_code, response_name)
    return None


# ============================================================
# RESPONSE VARIANT CRUD
# ============================================================

@router.post(
    "/{project_code}/versions/draft/responses/{response_name}/variants",
    response_model=ResponseVariantResponse,
    status_code=201,
)
def add_variant_endpoint(
    project_code: str,
    response_name: str,
    payload: ResponseVariantCreate,
    db: Session = Depends(get_db),
):
    """
    Add a variant to a response.
    
    Variants can have different languages, conditions, and components.
    Components include: text, buttons, image, custom (quickReplies, cards, etc.)
    """
    return add_response_variant(db, project_code, response_name, payload)


@router.get(
    "/{project_code}/versions/{status}/responses/{response_name}/variants",
    response_model=List[ResponseVariantResponse],
)
def list_variants_endpoint(
    project_code: str,
    status: str,
    response_name: str,
    db: Session = Depends(get_db),
):
    """List all variants for a response."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return list_response_variants(db, project_code, status, response_name)


@router.delete(
    "/{project_code}/versions/draft/responses/{response_name}/variants/{variant_id}",
    status_code=204,
)
def delete_variant_endpoint(
    project_code: str,
    response_name: str,
    variant_id: str,
    db: Session = Depends(get_db),
):
    """Delete a variant from a response."""
    delete_response_variant(db, project_code, response_name, variant_id)
    return None


# ============================================================
# BULK UPSERT
# ============================================================

@router.put(
    "/{project_code}/versions/draft/responses/{response_name}/upsert",
    response_model=ResponseResponse,
)
def upsert_response_endpoint(
    project_code: str,
    response_name: str,
    payload: ResponseUpsert,
    db: Session = Depends(get_db),
):
    """
    Create or update a response with all its variants.
    
    This is a convenience endpoint for bulk operations.
    Existing variants will be replaced with the new ones.
    """
    # Convert payload to dict format expected by service
    variants = []
    for var in payload.variants:
        var_dict = {
            "language_code": var.language_code,
            "priority": var.priority or 0,
            "components": [],
            "conditions": [],
        }
        
        # Add text component
        if var.text:
            var_dict["components"].append({
                "component_type": "text",
                "payload": var.text
            })
        
        # Add buttons component
        if var.buttons:
            var_dict["components"].append({
                "component_type": "buttons",
                "payload": var.buttons
            })
        
        # Add image component
        if var.image:
            var_dict["components"].append({
                "component_type": "image",
                "payload": var.image
            })
        
        # Add custom component
        if var.custom:
            var_dict["components"].append({
                "component_type": "custom",
                "payload": var.custom
            })
        
        # Add attachment component
        if var.attachment:
            var_dict["components"].append({
                "component_type": "attachment",
                "payload": var.attachment
            })
        
        # Add conditions
        if var.conditions:
            for cond in var.conditions:
                var_dict["conditions"].append({
                    "condition_type": cond.condition_type,
                    "slot_name": cond.slot_name,
                    "slot_value": cond.slot_value,
                })
        
        variants.append(var_dict)
    
    return upsert_response_with_variants(db, project_code, response_name, variants)
