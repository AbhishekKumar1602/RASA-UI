from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from app.core.dependencies import get_db
from app.schemas.intent import (
    IntentCreate,
    IntentResponse,
    IntentExampleUpsert,
    IntentUpdate,
)
from app.services.intent_service import (
    create_intent,
    upsert_intent_examples,
    list_intents,
    get_intent,
    get_intent_examples,
    update_intent,
    delete_intent,
    delete_intent_examples,
)


router = APIRouter(prefix="/projects", tags=["Intents"])


@router.post(
    "/{project_code}/versions/draft/intents",
    response_model=IntentResponse,
    status_code=201,
)
def create_intent_endpoint(
    project_code: str,
    payload: IntentCreate,
    db: Session = Depends(get_db),
):
    """Create a new intent in the draft version."""
    return create_intent(db, project_code=project_code, intent_name=payload.intent_name)


@router.get(
    "/{project_code}/versions/{status}/intents",
    response_model=List[IntentResponse],
)
def list_intents_endpoint(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    """List all intents for a version."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    intents = list_intents(db, project_code, status)
    return [IntentResponse(id=i.id, intent_name=i.intent_name) for i in intents]


@router.get(
    "/{project_code}/versions/{status}/intents/{intent_name}",
    response_model=IntentResponse,
)
def get_intent_endpoint(
    project_code: str,
    status: str,
    intent_name: str,
    db: Session = Depends(get_db),
):
    """Get a specific intent."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_intent(db, project_code, status, intent_name)


@router.put(
    "/{project_code}/versions/draft/intents/{intent_name}",
    response_model=IntentResponse,
)
def update_intent_endpoint(
    project_code: str,
    intent_name: str,
    payload: IntentUpdate,
    db: Session = Depends(get_db),
):
    """Update an intent in the draft version (rename)."""
    return update_intent(db, project_code, intent_name, payload)


@router.delete(
    "/{project_code}/versions/draft/intents/{intent_name}",
    status_code=204,
)
def delete_intent_endpoint(
    project_code: str,
    intent_name: str,
    db: Session = Depends(get_db),
):
    """Delete an intent from the draft version."""
    delete_intent(db, project_code, intent_name)
    return None


@router.post(
    "/{project_code}/versions/draft/intents/{intent_name}/examples",
)
def upsert_examples_endpoint(
    project_code: str,
    intent_name: str,
    payload: IntentExampleUpsert,
    db: Session = Depends(get_db),
):
    """Upsert examples for an intent in a specific language."""
    return upsert_intent_examples(
        db,
        project_code=project_code,
        intent_name=intent_name,
        language_code=payload.language_code,
        examples=payload.examples,
    )


@router.get(
    "/{project_code}/versions/{status}/intents/{intent_name}/examples",
)
def get_intent_examples_endpoint(
    project_code: str,
    status: str,
    intent_name: str,
    db: Session = Depends(get_db),
) -> Dict[str, List[str]]:
    """Get all examples for an intent grouped by language."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_intent_examples(db, project_code, status, intent_name)


@router.delete(
    "/{project_code}/versions/draft/intents/{intent_name}/examples/{language_code}",
    status_code=204,
)
def delete_intent_examples_endpoint(
    project_code: str,
    intent_name: str,
    language_code: str,
    db: Session = Depends(get_db),
):
    """Delete all examples for an intent in a specific language."""
    delete_intent_examples(db, project_code, intent_name, language_code)
    return None
