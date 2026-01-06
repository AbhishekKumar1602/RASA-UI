from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.lookup import (
    LookupCreate,
    LookupResponse,
    LookupExampleUpsert,
    LookupExampleResponse,
)
from app.services.lookup_service import (
    create_lookup,
    list_lookups,
    get_lookup,
    delete_lookup,
    upsert_lookup_examples,
    get_lookup_examples,
    delete_lookup_examples,
)


router = APIRouter(prefix="/projects", tags=["Lookups"])


@router.post(
    "/{project_code}/versions/draft/lookups",
    response_model=LookupResponse,
    status_code=201,
)
def create_lookup_endpoint(
    project_code: str,
    payload: LookupCreate,
    db: Session = Depends(get_db),
):
    """Create a new lookup in the draft version."""
    lookup = create_lookup(db, project_code, payload.lookup_name, payload.entity_key)
    return LookupResponse(
        id=lookup.id,
        lookup_name=lookup.lookup_name,
        entity_key=lookup.entity.entity_key,
    )


@router.get(
    "/{project_code}/versions/{status}/lookups",
    response_model=List[LookupResponse],
)
def list_lookups_endpoint(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    """List all lookups for a version."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return list_lookups(db, project_code, status)


@router.get(
    "/{project_code}/versions/{status}/lookups/{lookup_name}",
    response_model=LookupResponse,
)
def get_lookup_endpoint(
    project_code: str,
    status: str,
    lookup_name: str,
    db: Session = Depends(get_db),
):
    """Get a specific lookup."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_lookup(db, project_code, status, lookup_name)


@router.delete(
    "/{project_code}/versions/draft/lookups/{lookup_name}",
    status_code=204,
)
def delete_lookup_endpoint(
    project_code: str,
    lookup_name: str,
    db: Session = Depends(get_db),
):
    """Delete a lookup from the draft version."""
    delete_lookup(db, project_code, lookup_name)
    return None


@router.post(
    "/{project_code}/versions/draft/lookups/{lookup_name}/examples",
)
def upsert_lookup_examples_endpoint(
    project_code: str,
    lookup_name: str,
    payload: LookupExampleUpsert,
    db: Session = Depends(get_db),
):
    """Upsert examples for a lookup in a specific language."""
    return upsert_lookup_examples(
        db,
        project_code,
        lookup_name,
        payload.language_code,
        payload.examples,
    )


@router.get(
    "/{project_code}/versions/{status}/lookups/{lookup_name}/examples/{language_code}",
)
def get_lookup_examples_endpoint(
    project_code: str,
    status: str,
    lookup_name: str,
    language_code: str,
    db: Session = Depends(get_db),
):
    """Get examples for a lookup in a specific language."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_lookup_examples(db, project_code, status, lookup_name, language_code)


@router.delete(
    "/{project_code}/versions/draft/lookups/{lookup_name}/examples/{language_code}",
    status_code=204,
)
def delete_lookup_examples_endpoint(
    project_code: str,
    lookup_name: str,
    language_code: str,
    db: Session = Depends(get_db),
):
    """Delete all examples for a lookup in a specific language."""
    delete_lookup_examples(db, project_code, lookup_name, language_code)
    return None
