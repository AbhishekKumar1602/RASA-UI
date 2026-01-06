from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models import (
    Response, ResponseVariant, ResponseCondition, ResponseComponent,
    Version, Project, Language
)
from app.schemas.response import (
    ResponseCreate, ResponseUpdate,
    ResponseVariantCreate, ResponseVariantUpdate,
    ResponseComponentCreate
)


def get_version_by_status(db: Session, project_code: str, status: str) -> Version:
    """Get version by project code and status."""
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(404, "Project not found")
    
    version = db.query(Version).filter(
        Version.project_id == project.id,
        Version.status == status
    ).first()
    if not version:
        raise HTTPException(404, f"Version with status '{status}' not found")
    
    return version


# ============================================================
# RESPONSE CRUD
# ============================================================

def create_response(db: Session, project_code: str, payload: ResponseCreate) -> Response:
    """Create a new response in the draft version."""
    version = get_version_by_status(db, project_code, "draft")
    
    # Check for duplicate
    existing = db.query(Response).filter(
        Response.version_id == version.id,
        Response.name == payload.name
    ).first()
    if existing:
        raise HTTPException(400, f"Response '{payload.name}' already exists")
    
    # Validate response name (should start with utter_)
    if not payload.name.startswith("utter_"):
        raise HTTPException(
            400, 
            f"Response name '{payload.name}' should start with 'utter_'. "
            "Example: utter_greet, utter_goodbye"
        )
    
    response = Response(
        version_id=version.id,
        name=payload.name,
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    return response


def list_responses(db: Session, project_code: str, status: str) -> list:
    """List all responses for a version."""
    version = get_version_by_status(db, project_code, status)
    
    return db.query(Response).filter(
        Response.version_id == version.id
    ).order_by(Response.name).all()


def get_response(db: Session, project_code: str, status: str, response_name: str) -> Response:
    """Get a specific response by name with all variants."""
    version = get_version_by_status(db, project_code, status)
    
    response = db.query(Response).options(
        joinedload(Response.variants)
        .joinedload(ResponseVariant.conditions),
        joinedload(Response.variants)
        .joinedload(ResponseVariant.components),
        joinedload(Response.variants)
        .joinedload(ResponseVariant.language),
    ).filter(
        Response.version_id == version.id,
        Response.name == response_name
    ).first()
    
    if not response:
        raise HTTPException(404, f"Response '{response_name}' not found")
    
    return response


def update_response(db: Session, project_code: str, response_name: str, payload: ResponseUpdate) -> Response:
    """Update a response in the draft version."""
    version = get_version_by_status(db, project_code, "draft")
    
    response = db.query(Response).filter(
        Response.version_id == version.id,
        Response.name == response_name
    ).first()
    if not response:
        raise HTTPException(404, f"Response '{response_name}' not found")
    
    # Update name if provided
    if payload.name is not None:
        # Check for duplicate
        if payload.name != response_name:
            existing = db.query(Response).filter(
                Response.version_id == version.id,
                Response.name == payload.name
            ).first()
            if existing:
                raise HTTPException(400, f"Response '{payload.name}' already exists")
            
            # Validate new name
            if not payload.name.startswith("utter_"):
                raise HTTPException(
                    400, 
                    f"Response name '{payload.name}' should start with 'utter_'."
                )
        response.name = payload.name
    
    db.commit()
    db.refresh(response)
    return response


def delete_response(db: Session, project_code: str, response_name: str) -> None:
    """Delete a response from the draft version."""
    version = get_version_by_status(db, project_code, "draft")
    
    response = db.query(Response).filter(
        Response.version_id == version.id,
        Response.name == response_name
    ).first()
    if not response:
        raise HTTPException(404, f"Response '{response_name}' not found")
    
    db.delete(response)
    db.commit()


# ============================================================
# RESPONSE VARIANT CRUD
# ============================================================

def add_response_variant(
    db: Session, 
    project_code: str, 
    response_name: str, 
    payload: ResponseVariantCreate
) -> ResponseVariant:
    """Add a variant to a response."""
    version = get_version_by_status(db, project_code, "draft")
    
    response = db.query(Response).filter(
        Response.version_id == version.id,
        Response.name == response_name
    ).first()
    if not response:
        raise HTTPException(404, f"Response '{response_name}' not found")
    
    # Get language if provided
    language_id = None
    if payload.language_code:
        language = db.query(Language).filter(
            Language.language_code == payload.language_code
        ).first()
        if not language:
            raise HTTPException(404, f"Language '{payload.language_code}' not found")
        language_id = language.id
    
    variant = ResponseVariant(
        response_id=response.id,
        language_id=language_id,
        priority=payload.priority or 0,
    )
    db.add(variant)
    db.flush()
    
    # Add components
    for idx, comp in enumerate(payload.components or []):
        component = ResponseComponent(
            response_variant_id=variant.id,
            component_type=comp.component_type,
            payload=comp.payload,
            order_index=idx,
        )
        db.add(component)
    
    # Add conditions
    for idx, cond in enumerate(payload.conditions or []):
        condition = ResponseCondition(
            response_variant_id=variant.id,
            condition_type=cond.condition_type,
            slot_name=cond.slot_name,
            slot_value=cond.slot_value,
            order_index=idx,
        )
        db.add(condition)
    
    db.commit()
    db.refresh(variant)
    return variant


def list_response_variants(db: Session, project_code: str, status: str, response_name: str) -> list:
    """List all variants for a response."""
    version = get_version_by_status(db, project_code, status)
    
    response = db.query(Response).filter(
        Response.version_id == version.id,
        Response.name == response_name
    ).first()
    if not response:
        raise HTTPException(404, f"Response '{response_name}' not found")
    
    return db.query(ResponseVariant).options(
        joinedload(ResponseVariant.conditions),
        joinedload(ResponseVariant.components),
        joinedload(ResponseVariant.language),
    ).filter(
        ResponseVariant.response_id == response.id
    ).order_by(ResponseVariant.priority.desc()).all()


def delete_response_variant(db: Session, project_code: str, response_name: str, variant_id: str) -> None:
    """Delete a variant from a response."""
    version = get_version_by_status(db, project_code, "draft")
    
    response = db.query(Response).filter(
        Response.version_id == version.id,
        Response.name == response_name
    ).first()
    if not response:
        raise HTTPException(404, f"Response '{response_name}' not found")
    
    variant = db.query(ResponseVariant).filter(
        ResponseVariant.id == variant_id,
        ResponseVariant.response_id == response.id
    ).first()
    if not variant:
        raise HTTPException(404, f"Variant not found")
    
    db.delete(variant)
    db.commit()


# ============================================================
# UPSERT RESPONSE WITH VARIANTS (Convenience method)
# ============================================================

def upsert_response_with_variants(
    db: Session,
    project_code: str,
    response_name: str,
    variants: list
) -> Response:
    """
    Create or update a response with its variants.
    This is a convenience method for bulk operations.
    """
    version = get_version_by_status(db, project_code, "draft")
    
    # Validate name
    if not response_name.startswith("utter_"):
        raise HTTPException(
            400, 
            f"Response name '{response_name}' should start with 'utter_'."
        )
    
    # Get or create response
    response = db.query(Response).filter(
        Response.version_id == version.id,
        Response.name == response_name
    ).first()
    
    if not response:
        response = Response(
            version_id=version.id,
            name=response_name,
        )
        db.add(response)
        db.flush()
    else:
        # Delete existing variants
        db.query(ResponseComponent).filter(
            ResponseComponent.response_variant_id.in_(
                db.query(ResponseVariant.id).filter(
                    ResponseVariant.response_id == response.id
                )
            )
        ).delete(synchronize_session=False)
        
        db.query(ResponseCondition).filter(
            ResponseCondition.response_variant_id.in_(
                db.query(ResponseVariant.id).filter(
                    ResponseVariant.response_id == response.id
                )
            )
        ).delete(synchronize_session=False)
        
        db.query(ResponseVariant).filter(
            ResponseVariant.response_id == response.id
        ).delete(synchronize_session=False)
    
    # Add new variants
    for var_data in variants:
        language_id = None
        if var_data.get("language_code"):
            language = db.query(Language).filter(
                Language.language_code == var_data["language_code"]
            ).first()
            if language:
                language_id = language.id
        
        variant = ResponseVariant(
            response_id=response.id,
            language_id=language_id,
            priority=var_data.get("priority", 0),
        )
        db.add(variant)
        db.flush()
        
        # Add components
        for idx, comp in enumerate(var_data.get("components", [])):
            component = ResponseComponent(
                response_variant_id=variant.id,
                component_type=comp.get("component_type", "text"),
                payload=comp.get("payload"),
                order_index=idx,
            )
            db.add(component)
        
        # Add conditions
        for idx, cond in enumerate(var_data.get("conditions", [])):
            condition = ResponseCondition(
                response_variant_id=variant.id,
                condition_type=cond.get("condition_type", "slot"),
                slot_name=cond.get("slot_name"),
                slot_value=cond.get("slot_value"),
                order_index=idx,
            )
            db.add(condition)
    
    db.commit()
    db.refresh(response)
    return response

