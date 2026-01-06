from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models import Language, Entity, VersionLanguage
from app.models.lookup import Lookup, LookupExample
from app.services.common import get_version_by_status, get_draft_version


def create_lookup(db: Session, project_code: str, lookup_name: str, entity_key: str):
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
        raise HTTPException(404, "Entity not found in draft version")

    if entity.entity_type != "text":
        raise HTTPException(400, "Lookup is allowed only for text entities")

    if not entity.use_lookup:
        raise HTTPException(400, "Lookup detection is not enabled for this entity")

    existing = (
        db.query(Lookup)
        .filter(
            Lookup.version_id == version.id,
            Lookup.lookup_name == lookup_name,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Lookup already exists in this version")

    lookup = Lookup(
        lookup_name=lookup_name,
        entity_id=entity.id,
        version_id=version.id,
    )

    db.add(lookup)
    db.commit()
    db.refresh(lookup)

    return lookup


def list_lookups(db: Session, project_code: str, status: str):
    """List all lookups for a version."""
    version = get_version_by_status(db, project_code, status)

    lookups = (
        db.query(Lookup)
        .options(joinedload(Lookup.entity))
        .filter(Lookup.version_id == version.id)
        .order_by(Lookup.lookup_name)
        .all()
    )

    return [
        {
            "id": l.id,
            "lookup_name": l.lookup_name,
            "entity_key": l.entity.entity_key,
        }
        for l in lookups
    ]


def get_lookup(db: Session, project_code: str, status: str, lookup_name: str):
    """Get a specific lookup by name."""
    version = get_version_by_status(db, project_code, status)

    lookup = (
        db.query(Lookup)
        .options(joinedload(Lookup.entity))
        .filter(
            Lookup.version_id == version.id,
            Lookup.lookup_name == lookup_name,
        )
        .first()
    )
    if not lookup:
        raise HTTPException(404, "Lookup not found")

    return {
        "id": lookup.id,
        "lookup_name": lookup.lookup_name,
        "entity_key": lookup.entity.entity_key,
    }


def delete_lookup(db: Session, project_code: str, lookup_name: str):
    """Delete a lookup from the draft version."""
    version = get_draft_version(db, project_code)

    lookup = (
        db.query(Lookup)
        .filter(
            Lookup.version_id == version.id,
            Lookup.lookup_name == lookup_name,
        )
        .first()
    )
    if not lookup:
        raise HTTPException(404, "Lookup not found")

    # Delete examples first
    db.query(LookupExample).filter(LookupExample.lookup_id == lookup.id).delete()

    db.delete(lookup)
    db.commit()


def upsert_lookup_examples(
    db: Session,
    project_code: str,
    lookup_name: str,
    language_code: str,
    examples: list[str],
):
    """Upsert examples for a lookup in a specific language."""
    version = get_draft_version(db, project_code)

    lookup = (
        db.query(Lookup)
        .filter(
            Lookup.version_id == version.id,
            Lookup.lookup_name == lookup_name,
        )
        .first()
    )
    if not lookup:
        raise HTTPException(404, "Lookup not found")

    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
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

    db.query(LookupExample).filter(
        LookupExample.lookup_id == lookup.id,
        LookupExample.language_id == language.id,
    ).delete()

    for ex in examples:
        if ex.strip():
            db.add(
                LookupExample(
                    lookup_id=lookup.id,
                    language_id=language.id,
                    example=ex.strip(),
                )
            )

    db.commit()

    return {
        "lookup_name": lookup_name,
        "language_code": language_code,
        "example_count": len(examples),
    }


def get_lookup_examples(
    db: Session,
    project_code: str,
    status: str,
    lookup_name: str,
    language_code: str,
):
    version = get_version_by_status(db, project_code, status)

    lookup = (
        db.query(Lookup)
        .filter(
            Lookup.version_id == version.id,
            Lookup.lookup_name == lookup_name,
        )
        .first()
    )
    if not lookup:
        raise HTTPException(404, "Lookup not found")

    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )
    if not language:
        raise HTTPException(404, "Language not found")

    examples = (
        db.query(LookupExample)
        .filter(
            LookupExample.lookup_id == lookup.id,
            LookupExample.language_id == language.id,
        )
        .all()
    )

    return {
        "lookup_name": lookup_name,
        "language_code": language_code,
        "examples": [e.example for e in examples],
    }


def delete_lookup_examples(
    db: Session,
    project_code: str,
    lookup_name: str,
    language_code: str,
):
    version = get_draft_version(db, project_code)

    lookup = (
        db.query(Lookup)
        .filter(
            Lookup.version_id == version.id,
            Lookup.lookup_name == lookup_name,
        )
        .first()
    )
    if not lookup:
        raise HTTPException(404, "Lookup not found")

    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )
    if not language:
        raise HTTPException(404, "Language not found")

    db.query(LookupExample).filter(
        LookupExample.lookup_id == lookup.id,
        LookupExample.language_id == language.id,
    ).delete()

    db.commit()
