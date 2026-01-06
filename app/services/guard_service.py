from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models import (
    Intent,
    VersionLanguage,
    Language,
    IntentLocalization,
    IntentExample,
)


def validate_all_intents_for_version(
    db: Session,
    version_id: str,
    minimum: int = 10,
):
    """
    Promotion-time guard.
    Ensures:
    - At least one language is enabled for the version
    - At least one intent exists
    - Every intent has >= minimum examples for every enabled language
    """
    # Enabled languages
    version_languages = (
        db.query(VersionLanguage, Language)
        .join(Language, VersionLanguage.language_id == Language.id)
        .filter(VersionLanguage.version_id == version_id)
        .all()
    )

    if not version_languages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot promote: no languages enabled in version",
        )

    # Intents
    intents = db.query(Intent).filter(Intent.version_id == version_id).all()

    if not intents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot promote: no intents defined in version",
        )

    # Validate examples
    for intent in intents:
        for _, language in version_languages:
            localization = (
                db.query(IntentLocalization)
                .filter(
                    IntentLocalization.intent_id == intent.id,
                    IntentLocalization.language_id == language.id,
                )
                .first()
            )

            example_count = 0
            if localization:
                example_count = (
                    db.query(IntentExample)
                    .filter(IntentExample.intent_localization_id == localization.id)
                    .count()
                )

            if example_count < minimum:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=(
                        f"Intent '{intent.intent_name}' has only "
                        f"{example_count} examples for language "
                        f"'{language.language_code}'. "
                        f"Minimum required is {minimum}."
                    ),
                )

    return True
