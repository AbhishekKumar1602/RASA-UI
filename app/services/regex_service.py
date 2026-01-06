from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models import Language, Entity, VersionLanguage
from app.models.regex import Regex, RegexExample
from app.services.common import get_version_by_status, get_draft_version


def create_regex(db: Session, project_code: str, regex_name: str, entity_key: str):
    """Create a new regex in the draft version."""
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

    if not entity.use_regex:
        raise HTTPException(400, "Regex detection is not enabled for this entity")

    existing = (
        db.query(Regex)
        .filter(
            Regex.version_id == version.id,
            Regex.regex_name == regex_name,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Regex already exists in this version")

    regex = Regex(
        regex_name=regex_name,
        entity_id=entity.id,
        version_id=version.id,
    )

    db.add(regex)
    db.commit()
    db.refresh(regex)

    return regex


def list_regexes(db: Session, project_code: str, status: str):
    """List all regexes for a version."""
    version = get_version_by_status(db, project_code, status)

    regexes = (
        db.query(Regex)
        .options(joinedload(Regex.entity))
        .filter(Regex.version_id == version.id)
        .order_by(Regex.regex_name)
        .all()
    )

    return [
        {
            "id": r.id,
            "regex_name": r.regex_name,
            "entity_key": r.entity.entity_key,
        }
        for r in regexes
    ]


def get_regex(db: Session, project_code: str, status: str, regex_name: str):
    """Get a specific regex by name."""
    version = get_version_by_status(db, project_code, status)

    regex = (
        db.query(Regex)
        .options(joinedload(Regex.entity))
        .filter(
            Regex.version_id == version.id,
            Regex.regex_name == regex_name,
        )
        .first()
    )
    if not regex:
        raise HTTPException(404, "Regex not found")

    return {
        "id": regex.id,
        "regex_name": regex.regex_name,
        "entity_key": regex.entity.entity_key,
    }


def delete_regex(db: Session, project_code: str, regex_name: str):
    """Delete a regex from the draft version."""
    version = get_draft_version(db, project_code)

    regex = (
        db.query(Regex)
        .filter(
            Regex.version_id == version.id,
            Regex.regex_name == regex_name,
        )
        .first()
    )
    if not regex:
        raise HTTPException(404, "Regex not found")

    # Delete examples
    db.query(RegexExample).filter(RegexExample.regex_id == regex.id).delete()

    db.delete(regex)
    db.commit()


def upsert_regex_examples(
    db: Session,
    project_code: str,
    regex_name: str,
    language_code: str,
    examples: list[str],
):
    """Upsert examples for a regex in a specific language."""
    version = get_draft_version(db, project_code)

    regex = (
        db.query(Regex)
        .filter(
            Regex.version_id == version.id,
            Regex.regex_name == regex_name,
        )
        .first()
    )
    if not regex:
        raise HTTPException(404, "Regex not found")

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

    db.query(RegexExample).filter(
        RegexExample.regex_id == regex.id,
        RegexExample.language_id == language.id,
    ).delete()

    for ex in examples:
        if ex.strip():
            db.add(
                RegexExample(
                    regex_id=regex.id,
                    language_id=language.id,
                    example=ex.strip(),
                )
            )

    db.commit()

    return {
        "regex_name": regex_name,
        "language_code": language_code,
        "example_count": len(examples),
    }


def get_regex_examples(
    db: Session,
    project_code: str,
    status: str,
    regex_name: str,
    language_code: str,
):
    """Get examples for a regex in a specific language."""
    version = get_version_by_status(db, project_code, status)

    regex = (
        db.query(Regex)
        .filter(
            Regex.version_id == version.id,
            Regex.regex_name == regex_name,
        )
        .first()
    )
    if not regex:
        raise HTTPException(404, "Regex not found")

    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )
    if not language:
        raise HTTPException(404, "Language not found")

    examples = (
        db.query(RegexExample)
        .filter(
            RegexExample.regex_id == regex.id,
            RegexExample.language_id == language.id,
        )
        .all()
    )

    return {
        "regex_name": regex_name,
        "language_code": language_code,
        "examples": [e.example for e in examples],
    }


def delete_regex_examples(
    db: Session,
    project_code: str,
    regex_name: str,
    language_code: str,
):
    """Delete all examples for a regex in a specific language."""
    version = get_draft_version(db, project_code)

    regex = (
        db.query(Regex)
        .filter(
            Regex.version_id == version.id,
            Regex.regex_name == regex_name,
        )
        .first()
    )
    if not regex:
        raise HTTPException(404, "Regex not found")

    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )
    if not language:
        raise HTTPException(404, "Language not found")

    db.query(RegexExample).filter(
        RegexExample.regex_id == regex.id,
        RegexExample.language_id == language.id,
    ).delete()

    db.commit()
