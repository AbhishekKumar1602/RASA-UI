from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import (
    Intent,
    Language,
    VersionLanguage,
    IntentLocalization,
    IntentExample,
)
from app.services.common import get_version_by_status, get_draft_version


def create_intent(db: Session, project_code: str, intent_name: str):
    version = get_draft_version(db, project_code)

    existing = (
        db.query(Intent)
        .filter(
            Intent.version_id == version.id,
            Intent.intent_name == intent_name,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Intent already exists in draft version")

    intent = Intent(
        version_id=version.id,
        intent_name=intent_name,
    )

    db.add(intent)
    db.commit()
    db.refresh(intent)

    return intent


def list_intents(db: Session, project_code: str, status: str):
    version = get_version_by_status(db, project_code, status)

    return (
        db.query(Intent)
        .filter(Intent.version_id == version.id)
        .order_by(Intent.intent_name)
        .all()
    )


def get_intent(db: Session, project_code: str, status: str, intent_name: str):
    version = get_version_by_status(db, project_code, status)

    intent = (
        db.query(Intent)
        .filter(
            Intent.version_id == version.id,
            Intent.intent_name == intent_name,
        )
        .first()
    )
    if not intent:
        raise HTTPException(404, "Intent not found")

    return intent


def update_intent(db: Session, project_code: str, intent_name: str, payload):
    version = get_draft_version(db, project_code)

    intent = (
        db.query(Intent)
        .filter(
            Intent.version_id == version.id,
            Intent.intent_name == intent_name,
        )
        .first()
    )
    if not intent:
        raise HTTPException(404, "Intent not found")

    if payload.intent_name and payload.intent_name != intent_name:
        existing = (
            db.query(Intent)
            .filter(
                Intent.version_id == version.id,
                Intent.intent_name == payload.intent_name,
            )
            .first()
        )
        if existing:
            raise HTTPException(400, "Intent with this name already exists")
        intent.intent_name = payload.intent_name

    db.commit()
    db.refresh(intent)
    return intent


def delete_intent(db: Session, project_code: str, intent_name: str):
    version = get_draft_version(db, project_code)

    intent = (
        db.query(Intent)
        .filter(
            Intent.version_id == version.id,
            Intent.intent_name == intent_name,
        )
        .first()
    )
    if not intent:
        raise HTTPException(404, "Intent not found")

    localizations = (
        db.query(IntentLocalization)
        .filter(IntentLocalization.intent_id == intent.id)
        .all()
    )
    for loc in localizations:
        db.query(IntentExample).filter(
            IntentExample.intent_localization_id == loc.id
        ).delete()
    db.query(IntentLocalization).filter(
        IntentLocalization.intent_id == intent.id
    ).delete()

    db.delete(intent)
    db.commit()


def upsert_intent_examples(
    db: Session,
    project_code: str,
    intent_name: str,
    language_code: str,
    examples: list[str],
):
    version = get_draft_version(db, project_code)

    intent = (
        db.query(Intent)
        .filter(
            Intent.version_id == version.id,
            Intent.intent_name == intent_name,
        )
        .first()
    )
    if not intent:
        raise HTTPException(404, "Intent not found in draft version")

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

    localization = (
        db.query(IntentLocalization)
        .filter(
            IntentLocalization.intent_id == intent.id,
            IntentLocalization.language_id == language.id,
        )
        .first()
    )

    if not localization:
        localization = IntentLocalization(
            intent_id=intent.id,
            language_id=language.id,
        )
        db.add(localization)
        db.flush()

    db.query(IntentExample).filter(
        IntentExample.intent_localization_id == localization.id
    ).delete()

    for text in examples:
        if text.strip():
            db.add(
                IntentExample(
                    intent_localization_id=localization.id,
                    example=text.strip(),
                )
            )

    db.commit()

    return {
        "intent_name": intent_name,
        "language_code": language_code,
        "example_count": len(examples),
    }


def get_intent_examples(
    db: Session,
    project_code: str,
    status: str,
    intent_name: str,
):
    version = get_version_by_status(db, project_code, status)

    intent = (
        db.query(Intent)
        .filter(
            Intent.version_id == version.id,
            Intent.intent_name == intent_name,
        )
        .first()
    )
    if not intent:
        raise HTTPException(404, "Intent not found")

    localizations = (
        db.query(IntentLocalization)
        .filter(IntentLocalization.intent_id == intent.id)
        .all()
    )

    result = {}
    for loc in localizations:
        language = db.query(Language).filter(Language.id == loc.language_id).first()
        examples = (
            db.query(IntentExample)
            .filter(IntentExample.intent_localization_id == loc.id)
            .all()
        )
        result[language.language_code] = [ex.example for ex in examples]

    return result


def delete_intent_examples(
    db: Session,
    project_code: str,
    intent_name: str,
    language_code: str,
):
    version = get_draft_version(db, project_code)

    intent = (
        db.query(Intent)
        .filter(
            Intent.version_id == version.id,
            Intent.intent_name == intent_name,
        )
        .first()
    )
    if not intent:
        raise HTTPException(404, "Intent not found")

    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )
    if not language:
        raise HTTPException(404, "Language not found")

    localization = (
        db.query(IntentLocalization)
        .filter(
            IntentLocalization.intent_id == intent.id,
            IntentLocalization.language_id == language.id,
        )
        .first()
    )
    if not localization:
        raise HTTPException(404, "No examples found for this language")

    db.query(IntentExample).filter(
        IntentExample.intent_localization_id == localization.id
    ).delete()

    db.delete(localization)
    db.commit()
