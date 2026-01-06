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
    Story,
    StoryStep,
    StorySlotEvent,
    Rule,
    RuleStep,
    RuleSlotEvent,
)


# -------------------------------------------------
# NLU QUERIES
# -------------------------------------------------


def fetch_intents(db: Session, version_id: str, language_code: str) -> dict:
    """
    Returns:
    {
        intent_name: [example, example, ...]
    }
    """
    # First get the language
    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )

    if not language:
        return {}

    result = {}

    # Query intents with their localizations and examples
    intents = (
        db.query(Intent)
        .options(
            joinedload(Intent.localizations).joinedload(IntentLocalization.examples)
        )
        .filter(Intent.version_id == version_id)
        .all()
    )

    for intent in intents:
        # Find localization for this language
        for localization in intent.localizations:
            if localization.language_id == language.id:
                examples = [ex.example for ex in localization.examples]
                if examples:
                    result[intent.intent_name] = examples
                break

    return result


def fetch_regexes(db: Session, version_id: str, language_code: str) -> dict:
    """
    Returns:
    {
        regex_name: [pattern, pattern, ...]
    }
    """
    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )

    if not language:
        return {}

    result = {}

    regexes = (
        db.query(Regex)
        .options(joinedload(Regex.examples))
        .filter(Regex.version_id == version_id)
        .all()
    )

    for regex in regexes:
        examples = [
            ex.example for ex in regex.examples if ex.language_id == language.id
        ]
        if examples:
            result[regex.regex_name] = examples

    return result


def fetch_lookups(db: Session, version_id: str, language_code: str) -> dict:
    """
    Returns:
    {
        lookup_name: [value, value, ...]
    }
    """
    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )

    if not language:
        return {}

    result = {}

    lookups = (
        db.query(Lookup)
        .options(joinedload(Lookup.examples))
        .filter(Lookup.version_id == version_id)
        .all()
    )

    for lookup in lookups:
        examples = [
            ex.example for ex in lookup.examples if ex.language_id == language.id
        ]
        if examples:
            result[lookup.lookup_name] = examples

    return result


def fetch_synonyms(db: Session, version_id: str, language_code: str) -> dict:
    """
    Returns:
    {
        canonical_value: [synonym, synonym, ...]
    }
    """
    language = (
        db.query(Language).filter(Language.language_code == language_code).first()
    )

    if not language:
        return {}

    result = {}

    synonyms = (
        db.query(Synonym)
        .options(joinedload(Synonym.examples))
        .filter(Synonym.version_id == version_id)
        .all()
    )

    for syn in synonyms:
        examples = [ex.example for ex in syn.examples if ex.language_id == language.id]
        if examples:
            result[syn.canonical_value] = examples

    return result


# -------------------------------------------------
# STORY QUERIES
# -------------------------------------------------


def fetch_stories(db: Session, version_id: str):
    """
    Fetch all stories for a version with eager loading
    """
    return (
        db.query(Story)
        .options(
            joinedload(Story.steps).joinedload(StoryStep.intent),
            joinedload(Story.steps).joinedload(StoryStep.action),
            joinedload(Story.steps).joinedload(StoryStep.form),
            joinedload(Story.steps)
            .joinedload(StoryStep.slot_events)
            .joinedload(StorySlotEvent.slot),
        )
        .filter(Story.version_id == version_id)
        .order_by(Story.name)
        .all()
    )


def fetch_story_steps(db: Session, story_id: str):
    """
    Fetch all steps for a story with eager loading
    """
    return (
        db.query(StoryStep)
        .options(
            joinedload(StoryStep.intent),
            joinedload(StoryStep.action),
            joinedload(StoryStep.form),
            joinedload(StoryStep.slot_events).joinedload(StorySlotEvent.slot),
        )
        .filter(StoryStep.story_id == story_id)
        .order_by(
            StoryStep.timeline_index,
            StoryStep.step_order,
        )
        .all()
    )


def fetch_story_slot_events(db: Session, step_id: str):
    """
    Fetch all slot events for a story step
    """
    return (
        db.query(StorySlotEvent)
        .options(joinedload(StorySlotEvent.slot))
        .filter(StorySlotEvent.story_step_id == step_id)
        .order_by(StorySlotEvent.id)
        .all()
    )


# -------------------------------------------------
# RULE QUERIES
# -------------------------------------------------


def fetch_rules(db: Session, version_id: str):
    """
    Fetch all rules for a version with eager loading
    """
    return (
        db.query(Rule)
        .options(
            joinedload(Rule.conditions),
            joinedload(Rule.steps).joinedload(RuleStep.intent),
            joinedload(Rule.steps).joinedload(RuleStep.action),
            joinedload(Rule.steps)
            .joinedload(RuleStep.slot_events)
            .joinedload(RuleSlotEvent.slot),
        )
        .filter(Rule.version_id == version_id)
        .order_by(Rule.name)
        .all()
    )


def fetch_rule_steps(db: Session, rule_id: str):
    """
    Fetch all steps for a rule with eager loading
    """
    return (
        db.query(RuleStep)
        .options(
            joinedload(RuleStep.intent),
            joinedload(RuleStep.action),
            joinedload(RuleStep.slot_events).joinedload(RuleSlotEvent.slot),
        )
        .filter(RuleStep.rule_id == rule_id)
        .order_by(RuleStep.step_order)
        .all()
    )


def fetch_rule_slot_events(db: Session, step_id: str):
    """
    Fetch all slot events for a rule step
    """
    return (
        db.query(RuleSlotEvent)
        .options(joinedload(RuleSlotEvent.slot))
        .filter(RuleSlotEvent.rule_step_id == step_id)
        .order_by(RuleSlotEvent.id)
        .all()
    )
