from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models import Language, Entity, VersionLanguage
from app.models.synonym import Synonym, SynonymExample
from app.services.common import get_version_by_status, get_draft_version


def upsert_synonym(db: Session, project_code: str, payload):
    """Create or update a synonym in the draft version."""
    version = get_draft_version(db, project_code)

    entity = (
        db.query(Entity)
        .filter(
            Entity.version_id == version.id,
            Entity.entity_key == payload.entity_key,
        )
        .first()
    )
    if not entity:
        raise HTTPException(404, "Entity not found in draft version")

    if entity.entity_type != "text":
        raise HTTPException(400, "Synonyms are allowed only for text entities")

    language = (
        db.query(Language)
        .filter(Language.language_code == payload.language_code)
        .first()
    )
    if not language:
        raise HTTPException(404, "Language not found")

    enabled = (
        db.query(VersionLanguage)
        .filter(
            VersionLanguage.version_id == version.id,
            VersionLanguage.language_id == language.id,
        )
        .first()
    )
    if not enabled:
        raise HTTPException(400, "Language not enabled in draft version")

    synonym = (
        db.query(Synonym)
        .filter(
            Synonym.version_id == version.id,
            Synonym.entity_id == entity.id,
            Synonym.canonical_value == payload.canonical_value,
        )
        .first()
    )

    if not synonym:
        synonym = Synonym(
            version_id=version.id,
            entity_id=entity.id,
            canonical_value=payload.canonical_value,
        )
        db.add(synonym)
        db.flush()

    # Replace examples
    db.query(SynonymExample).filter(
        SynonymExample.synonym_id == synonym.id,
        SynonymExample.language_id == language.id,
    ).delete()

    for ex in payload.examples:
        if ex.strip():
            db.add(
                SynonymExample(
                    synonym_id=synonym.id,
                    language_id=language.id,
                    example=ex.strip(),
                )
            )

    db.commit()

    return {
        "entity_key": payload.entity_key,
        "canonical_value": payload.canonical_value,
        "language_code": payload.language_code,
        "example_count": len(payload.examples),
    }


def list_synonyms(db: Session, project_code: str, status: str):
    """List all synonyms for a version."""
    version = get_version_by_status(db, project_code, status)

    synonyms = (
        db.query(Synonym)
        .options(joinedload(Synonym.entity))
        .filter(Synonym.version_id == version.id)
        .order_by(Synonym.canonical_value)
        .all()
    )

    return [
        {
            "id": s.id,
            "entity_key": s.entity.entity_key,
            "canonical_value": s.canonical_value,
        }
        for s in synonyms
    ]


def get_synonym(
    db: Session,
    project_code: str,
    status: str,
    entity_key: str,
    canonical_value: str,
):
    """Get a specific synonym."""
    version = get_version_by_status(db, project_code, status)

    entity = (
        db.query(Entity)
        .filter(
            Entity.version_id == version.id,
            Entity.entity_key == entity_key,
        )
        .first()
    )
    if not entity:
        raise HTTPException(404, "Entity not found")

    synonym = (
        db.query(Synonym)
        .filter(
            Synonym.version_id == version.id,
            Synonym.entity_id == entity.id,
            Synonym.canonical_value == canonical_value,
        )
        .first()
    )
    if not synonym:
        raise HTTPException(404, "Synonym not found")

    return {
        "id": synonym.id,
        "entity_key": entity_key,
        "canonical_value": synonym.canonical_value,
    }


def delete_synonym(db: Session, project_code: str, entity_key: str, canonical_value: str):
    """Delete a synonym from the draft version."""
    version = get_draft_version(db, project_code)

    entity = (
        db.query(Entity)
        .filter(
            Entity.version_id == version.id,
            Entity.entity_key == entity_key,
        )
        .first()
    )
    if not entity:
        raise HTTPException(404, "Entity not found")

    synonym = (
        db.query(Synonym)
        .filter(
            Synonym.version_id == version.id,
            Synonym.entity_id == entity.id,
            Synonym.canonical_value == canonical_value,
        )
        .first()
    )
    if not synonym:
        raise HTTPException(404, "Synonym not found")

    # Delete examples
    db.query(SynonymExample).filter(SynonymExample.synonym_id == synonym.id).delete()

    db.delete(synonym)
    db.commit()
