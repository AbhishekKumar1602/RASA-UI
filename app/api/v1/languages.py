from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.language import LanguageCreate, LanguageResponse
from app.services.language_service import create_language, list_languages
from app.models.language import Language


router = APIRouter(prefix="/languages", tags=["Languages"])


@router.post(
    "/",
    response_model=LanguageResponse,
    status_code=201,
)
def create_new_language(
    payload: LanguageCreate,
    db: Session = Depends(get_db),
):
    """Create a new language."""
    existing = (
        db.query(Language)
        .filter(Language.language_code == payload.language_code)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Language with this code already exists",
        )

    return create_language(db, payload.language_code, payload.language_name)


@router.get(
    "/",
    response_model=List[LanguageResponse],
)
def get_languages(db: Session = Depends(get_db)):
    """List all languages."""
    return list_languages(db)
