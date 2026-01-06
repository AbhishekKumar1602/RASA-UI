from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.utils.export_queries import (
    fetch_intents,
    fetch_synonyms,
    fetch_regexes,
    fetch_lookups,
)
from app.utils.nlu_yaml_writer import (
    write_header,
    write_intent_block,
    write_synonym_block,
    write_regex_block,
    write_lookup_block,
)

MIN_INTENT_EXAMPLES = 10


def export_nlu_yaml(
    db: Session,
    version_id: str,
    language_code: str,
):
    intents = fetch_intents(db, version_id, language_code)
    synonyms = fetch_synonyms(db, version_id, language_code)
    regexes = fetch_regexes(db, version_id, language_code)
    lookups = fetch_lookups(db, version_id, language_code)

    if not intents:
        raise HTTPException(400, "No NLU intents found for export")

    for intent, examples in intents.items():
        if len(examples) < MIN_INTENT_EXAMPLES:
            raise HTTPException(
                400,
                f"Intent '{intent}' has only {len(examples)} examples",
            )

    yaml = write_header()

    for intent in sorted(intents):
        yaml += write_intent_block(intent, intents[intent])

    for canonical in sorted(synonyms):
        yaml += write_synonym_block(canonical, synonyms[canonical])

    for name in sorted(regexes):
        yaml += write_regex_block(name, regexes[name])

    for name in sorted(lookups):
        yaml += write_lookup_block(name, lookups[name])

    return yaml
