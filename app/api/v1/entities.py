from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.entity import EntityCreate, EntityResponse, EntityUpdate
from app.services.entity_service import (
    create_entity,
    list_entities,
    get_entity,
    update_entity,
    delete_entity,
)


router = APIRouter(prefix="/projects", tags=["Entities"])


@router.post(
    "/{project_code}/versions/draft/entities",
    response_model=EntityResponse,
    status_code=201,
)
def create_entity_endpoint(
    project_code: str,
    payload: EntityCreate,
    db: Session = Depends(get_db),
):
    entity, roles, groups = create_entity(db, project_code, payload)
    return EntityResponse(
        id=entity.id,
        entity_key=entity.entity_key,
        entity_type=entity.entity_type,
        use_regex=entity.use_regex,
        use_lookup=entity.use_lookup,
        influence_conversation=entity.influence_conversation,
        roles=roles,
        groups=groups,
    )


@router.get(
    "/{project_code}/versions/{status}/entities",
    response_model=List[EntityResponse],
)
def list_entities_endpoint(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    """List all entities for a version."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return list_entities(db, project_code, status)


@router.get(
    "/{project_code}/versions/{status}/entities/{entity_key}",
    response_model=EntityResponse,
)
def get_entity_endpoint(
    project_code: str,
    status: str,
    entity_key: str,
    db: Session = Depends(get_db),
):
    """Get a specific entity."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_entity(db, project_code, status, entity_key)


@router.put(
    "/{project_code}/versions/draft/entities/{entity_key}",
    response_model=EntityResponse,
)
def update_entity_endpoint(
    project_code: str,
    entity_key: str,
    payload: EntityUpdate,
    db: Session = Depends(get_db),
):
    """Update an entity in the draft version."""
    return update_entity(db, project_code, entity_key, payload)


@router.delete(
    "/{project_code}/versions/draft/entities/{entity_key}",
    status_code=204,
)
def delete_entity_endpoint(
    project_code: str,
    entity_key: str,
    db: Session = Depends(get_db),
):
    """Delete an entity from the draft version."""
    delete_entity(db, project_code, entity_key)
    return None
