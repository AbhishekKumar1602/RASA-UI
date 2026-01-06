from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.synonym import SynonymUpsert, SynonymResponse
from app.services.synonym_service import upsert_synonym


router = APIRouter(prefix="/projects", tags=["Synonyms"])


@router.post(
    "/{project_code}/versions/draft/synonyms",
    response_model=SynonymResponse,
    status_code=201,
)
def upsert_synonym_endpoint(
    project_code: str,
    payload: SynonymUpsert,
    db: Session = Depends(get_db),
):
    """Create or update a synonym in the draft version."""
    return upsert_synonym(db, project_code, payload)
