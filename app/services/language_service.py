from sqlalchemy.orm import Session
from app.models.language import Language


def create_language(db: Session, language_code: str, language_name: str):
    """Create a new language."""
    language = Language(
        language_code=language_code,
        language_name=language_name,
    )
    db.add(language)
    db.commit()
    db.refresh(language)
    return language


def list_languages(db: Session):
    """List all languages."""
    return db.query(Language).order_by(Language.language_code).all()
