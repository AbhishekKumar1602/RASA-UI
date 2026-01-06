from fastapi import HTTPException
from sqlalchemy.orm import Session, joinedload

from app.models import (
    Intent,
    IntentLocalization,
    IntentExample,
    Regex,
    RegexExample,
    Lookup,
    LookupExample,
    Synonym,
    SynonymExample,
    Language,
)

MIN_INTENT_EXAMPLES = 10


def export_nlu_yaml(db: Session, version_id: str, language_code: str) -> dict:
    """
    Export Rasa nlu.yml for a single VERSION + LANGUAGE
    """

    # -------------------------------------------------
    # LANGUAGE
    # -------------------------------------------------
    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )
    if not language:
        raise HTTPException(404, f"Language '{language_code}' not found")

    nlu_blocks = []

    # -------------------------------------------------
    # INTENTS
    # -------------------------------------------------
    intents = (
        db.query(Intent)
        .options(
            joinedload(Intent.localizations).joinedload(IntentLocalization.examples)
        )
        .filter(Intent.version_id == version_id)
        .order_by(Intent.intent_name)
        .all()
    )

    for intent in intents:
        # Find localization for this language
        localization = None
        for loc in intent.localizations:
            if loc.language_id == language.id:
                localization = loc
                break

        if not localization:
            continue

        examples = localization.examples
        if not examples:
            continue

        if len(examples) < MIN_INTENT_EXAMPLES:
            raise HTTPException(
                400,
                f"Intent '{intent.intent_name}' has only {len(examples)} examples. "
                f"Minimum required is {MIN_INTENT_EXAMPLES}.",
            )

        # Sort by created_at
        sorted_examples = sorted(examples, key=lambda e: e.created_at)

        nlu_blocks.append(
            {
                "intent": intent.intent_name,
                "examples": "\n".join(f"- {e.example}" for e in sorted_examples),
            }
        )

    if not nlu_blocks:
        raise HTTPException(400, "No NLU data found for export")

    # -------------------------------------------------
    # REGEX FEATURES
    # -------------------------------------------------
    regexes = (
        db.query(Regex)
        .options(joinedload(Regex.examples))
        .filter(Regex.version_id == version_id)
        .order_by(Regex.regex_name)
        .all()
    )

    for regex in regexes:
        examples = [ex for ex in regex.examples if ex.language_id == language.id]

        if examples:
            sorted_examples = sorted(examples, key=lambda e: e.created_at)
            nlu_blocks.append(
                {
                    "regex": regex.regex_name,
                    "examples": "\n".join(f"- {e.example}" for e in sorted_examples),
                }
            )

    # -------------------------------------------------
    # LOOKUP TABLES
    # -------------------------------------------------
    lookups = (
        db.query(Lookup)
        .options(joinedload(Lookup.examples))
        .filter(Lookup.version_id == version_id)
        .order_by(Lookup.lookup_name)
        .all()
    )

    for lookup in lookups:
        examples = [ex for ex in lookup.examples if ex.language_id == language.id]

        if examples:
            sorted_examples = sorted(examples, key=lambda e: e.created_at)
            nlu_blocks.append(
                {
                    "lookup": lookup.lookup_name,
                    "examples": "\n".join(f"- {e.example}" for e in sorted_examples),
                }
            )

    # -------------------------------------------------
    # SYNONYMS
    # -------------------------------------------------
    synonyms = (
        db.query(Synonym)
        .options(joinedload(Synonym.examples))
        .filter(Synonym.version_id == version_id)
        .order_by(Synonym.canonical_value)
        .all()
    )

    for synonym in synonyms:
        examples = [ex for ex in synonym.examples if ex.language_id == language.id]

        if examples:
            sorted_examples = sorted(examples, key=lambda e: e.created_at)
            nlu_blocks.append(
                {
                    "synonym": synonym.canonical_value,
                    "examples": "\n".join(f"- {e.example}" for e in sorted_examples),
                }
            )

    # -------------------------------------------------
    # FINAL YAML STRUCTURE
    # -------------------------------------------------
    return {
        "version": "3.1",
        "nlu": nlu_blocks,
    }
