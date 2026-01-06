from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.regex import (
    RegexCreate,
    RegexResponse,
    RegexExampleUpsert,
)
from app.services.regex_service import (
    create_regex,
    list_regexes,
    get_regex,
    delete_regex,
    upsert_regex_examples,
    get_regex_examples,
    delete_regex_examples,
)


router = APIRouter(prefix="/projects", tags=["Regexes"])


@router.post(
    "/{project_code}/versions/draft/regexes",
    response_model=RegexResponse,
    status_code=201,
)
def create_regex_endpoint(
    project_code: str,
    payload: RegexCreate,
    db: Session = Depends(get_db),
):
    """Create a new regex in the draft version."""
    regex = create_regex(db, project_code, payload.regex_name, payload.entity_key)
    return RegexResponse(
        id=regex.id,
        regex_name=regex.regex_name,
        entity_key=regex.entity.entity_key,
    )


@router.get(
    "/{project_code}/versions/{status}/regexes",
    response_model=List[RegexResponse],
)
def list_regexes_endpoint(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    """List all regexes for a version."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return list_regexes(db, project_code, status)


@router.get(
    "/{project_code}/versions/{status}/regexes/{regex_name}",
    response_model=RegexResponse,
)
def get_regex_endpoint(
    project_code: str,
    status: str,
    regex_name: str,
    db: Session = Depends(get_db),
):
    """Get a specific regex."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_regex(db, project_code, status, regex_name)


@router.delete(
    "/{project_code}/versions/draft/regexes/{regex_name}",
    status_code=204,
)
def delete_regex_endpoint(
    project_code: str,
    regex_name: str,
    db: Session = Depends(get_db),
):
    """Delete a regex from the draft version."""
    delete_regex(db, project_code, regex_name)
    return None


@router.post(
    "/{project_code}/versions/draft/regexes/{regex_name}/examples",
)
def upsert_regex_examples_endpoint(
    project_code: str,
    regex_name: str,
    payload: RegexExampleUpsert,
    db: Session = Depends(get_db),
):
    """Upsert examples for a regex in a specific language."""
    return upsert_regex_examples(
        db,
        project_code,
        regex_name,
        payload.language_code,
        payload.examples,
    )


@router.get(
    "/{project_code}/versions/{status}/regexes/{regex_name}/examples/{language_code}",
)
def get_regex_examples_endpoint(
    project_code: str,
    status: str,
    regex_name: str,
    language_code: str,
    db: Session = Depends(get_db),
):
    """Get examples for a regex in a specific language."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_regex_examples(db, project_code, status, regex_name, language_code)


@router.delete(
    "/{project_code}/versions/draft/regexes/{regex_name}/examples/{language_code}",
    status_code=204,
)
def delete_regex_examples_endpoint(
    project_code: str,
    regex_name: str,
    language_code: str,
    db: Session = Depends(get_db),
):
    """Delete all examples for a regex in a specific language."""
    delete_regex_examples(db, project_code, regex_name, language_code)
    return None
