from fastapi import APIRouter

from app.api.v1 import (
    languages,
    projects,
    intents,
    entities,
    regexes,
    lookups,
    synonyms,
    slots,
    forms,
    actions,
    responses,
    stories,
    rules,
    session_config,
    export,
)

router = APIRouter()

router.include_router(languages.router)
router.include_router(projects.router)
router.include_router(intents.router)
router.include_router(entities.router)
router.include_router(regexes.router)
router.include_router(lookups.router)
router.include_router(synonyms.router)
router.include_router(slots.router)
router.include_router(forms.router)
router.include_router(actions.router)
router.include_router(responses.router)
router.include_router(stories.router)
router.include_router(rules.router)
router.include_router(session_config.router)
router.include_router(export.router)
