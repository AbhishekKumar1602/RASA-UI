from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.story import (
    StoryCreate,
    StoryResponse,
    StoryUpdate,
    StoryStepCreate,
    StoryStepResponse,
    StoryStepUpdate,
    StorySlotEventCreate,
    StorySlotEventResponse,
    StoryStepEntityCreate,
    StoryStepEntityResponse,
    OrGroupCreate,
    OrGroupResponse,
)
from app.services.story_service import (
    create_story,
    list_stories,
    get_story,
    update_story,
    delete_story,
    add_story_step,
    list_story_steps,
    update_story_step,
    delete_story_step,
    add_story_slot_event,
    delete_story_slot_event,
    add_story_step_entity,
    list_story_step_entities,
    delete_story_step_entity,
)


router = APIRouter(prefix="/projects", tags=["Stories"])


# -------------------------------------------------
# STORY CRUD
# -------------------------------------------------

@router.post(
    "/{project_code}/versions/draft/stories",
    response_model=StoryResponse,
    status_code=201,
)
def create_story_api(
    project_code: str,
    payload: StoryCreate,
    db: Session = Depends(get_db),
):
    """Create a new story in the draft version."""
    return create_story(db, project_code, payload)


@router.get(
    "/{project_code}/versions/{status}/stories",
    response_model=List[StoryResponse],
)
def list_stories_api(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    """List all stories for a version."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    stories = list_stories(db, project_code, status)
    return [StoryResponse(id=s.id, name=s.name) for s in stories]


@router.get(
    "/{project_code}/versions/{status}/stories/{story_name}",
    response_model=StoryResponse,
)
def get_story_api(
    project_code: str,
    status: str,
    story_name: str,
    db: Session = Depends(get_db),
):
    """Get a specific story."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_story(db, project_code, status, story_name)


@router.put(
    "/{project_code}/versions/draft/stories/{story_name}",
    response_model=StoryResponse,
)
def update_story_api(
    project_code: str,
    story_name: str,
    payload: StoryUpdate,
    db: Session = Depends(get_db),
):
    """Update a story in the draft version."""
    return update_story(db, project_code, story_name, payload)


@router.delete(
    "/{project_code}/versions/draft/stories/{story_name}",
    status_code=204,
)
def delete_story_api(
    project_code: str,
    story_name: str,
    db: Session = Depends(get_db),
):
    """Delete a story from the draft version."""
    delete_story(db, project_code, story_name)
    return None


# -------------------------------------------------
# STORY STEPS
# -------------------------------------------------

@router.post(
    "/stories/{story_id}/steps",
    response_model=StoryStepResponse,
    status_code=201,
)
def add_story_step_api(
    story_id: str,
    payload: StoryStepCreate,
    db: Session = Depends(get_db),
):
    """
    Add a step to a story.
    
    For action steps, provide ONE of:
    - action_name: Custom action (e.g., "action_save_to_db")
    - response_name: Utterance (e.g., "utter_greet")
    - form_name: Form activation (e.g., "request_form")
    
    For intent steps with entities:
    ```json
    {
        "step_type": "intent",
        "intent_name": "inform",
        "timeline_index": 0,
        "step_order": 0,
        "entities": [
            {"entity_key": "city", "value": "Delhi"}
        ]
    }
    ```
    
    For OR conditions (multiple intents):
    ```json
    {
        "step_type": "or",
        "timeline_index": 0,
        "step_order": 2,
        "or_intents": ["affirm", "deny"]
    }
    ```
    """
    step = add_story_step(db, story_id, payload)
    
    # Build entity response
    entities = []
    if hasattr(step, 'entities') and step.entities:
        entities = [
            StoryStepEntityResponse(
                id=e.id,
                entity_key=e.entity.entity_key,
                value=e.value,
                role=e.role,
                group=e.group,
            )
            for e in step.entities
        ]
    
    return StoryStepResponse(
        id=step.id,
        step_type=step.step_type,
        timeline_index=step.timeline_index,
        step_order=step.step_order,
        intent_name=step.intent.intent_name if step.intent else None,
        action_name=step.action.name if step.action else None,
        response_name=step.response.name if step.response else None,
        form_name=step.form.name if step.form else None,
        active_loop_value=step.active_loop_value,
        checkpoint_name=step.checkpoint_name,
        or_group_id=step.or_group_id,
        entities=entities,
    )


@router.get(
    "/stories/{story_id}/steps",
    response_model=List[StoryStepResponse],
)
def list_story_steps_api(
    story_id: str,
    db: Session = Depends(get_db),
):
    """List all steps for a story."""
    steps = list_story_steps(db, story_id)
    return [
        StoryStepResponse(
            id=s["id"],
            step_type=s["step_type"],
            timeline_index=s["timeline_index"],
            step_order=s["step_order"],
            intent_name=s.get("intent_name"),
            action_name=s.get("action_name"),
            response_name=s.get("response_name"),
            form_name=s.get("form_name"),
            active_loop_value=s.get("active_loop_value"),
            checkpoint_name=s.get("checkpoint_name"),
            or_group_id=s.get("or_group_id"),
            entities=[
                StoryStepEntityResponse(
                    id=e["id"],
                    entity_key=e["entity_key"],
                    value=e.get("value"),
                    role=e.get("role"),
                    group=e.get("group"),
                )
                for e in s.get("entities", [])
            ],
        )
        for s in steps
    ]


@router.put(
    "/story-steps/{step_id}",
    response_model=StoryStepResponse,
)
def update_story_step_api(
    step_id: str,
    payload: StoryStepUpdate,
    db: Session = Depends(get_db),
):
    """Update a story step."""
    result = update_story_step(db, step_id, payload)
    return StoryStepResponse(
        id=result["id"],
        step_type=result["step_type"],
        timeline_index=result["timeline_index"],
        step_order=result["step_order"],
        intent_name=result.get("intent_name"),
        action_name=result.get("action_name"),
        response_name=result.get("response_name"),
        form_name=result.get("form_name"),
        active_loop_value=result.get("active_loop_value"),
        checkpoint_name=result.get("checkpoint_name"),
        or_group_id=result.get("or_group_id"),
    )


@router.delete(
    "/story-steps/{step_id}",
    status_code=204,
)
def delete_story_step_api(
    step_id: str,
    db: Session = Depends(get_db),
):
    """Delete a story step."""
    delete_story_step(db, step_id)
    return None


# -------------------------------------------------
# STORY SLOT EVENTS
# -------------------------------------------------

@router.post(
    "/story-steps/{step_id}/slot-events",
    response_model=StorySlotEventResponse,
    status_code=201,
)
def add_story_slot_event_api(
    step_id: str,
    payload: StorySlotEventCreate,
    db: Session = Depends(get_db),
):
    """Add a slot event to a story step."""
    event = add_story_slot_event(db, step_id, payload)
    return StorySlotEventResponse(
        id=event.id,
        slot_name=event.slot.name,
        value=event.value,
    )


@router.delete(
    "/story-slot-events/{event_id}",
    status_code=204,
)
def delete_story_slot_event_api(
    event_id: str,
    db: Session = Depends(get_db),
):
    """Delete a story slot event."""
    delete_story_slot_event(db, event_id)
    return None


# -------------------------------------------------
# STORY STEP ENTITIES (NEW)
# -------------------------------------------------

@router.post(
    "/story-steps/{step_id}/entities",
    response_model=StoryStepEntityResponse,
    status_code=201,
)
def add_story_step_entity_api(
    step_id: str,
    payload: StoryStepEntityCreate,
    db: Session = Depends(get_db),
):
    """
    Add an entity annotation to a story step.
    
    Only allowed for intent steps.
    
    Example:
    ```json
    {
        "entity_key": "city",
        "value": "Delhi"
    }
    ```
    
    This generates RASA YAML:
    ```yaml
    - intent: inform
      entities:
        - city: Delhi
    ```
    """
    result = add_story_step_entity(db, step_id, payload)
    return StoryStepEntityResponse(
        id=result["id"],
        entity_key=result["entity_key"],
        value=result.get("value"),
        role=result.get("role"),
        group=result.get("group"),
    )


@router.get(
    "/story-steps/{step_id}/entities",
    response_model=List[StoryStepEntityResponse],
)
def list_story_step_entities_api(
    step_id: str,
    db: Session = Depends(get_db),
):
    """List all entity annotations for a story step."""
    entities = list_story_step_entities(db, step_id)
    return [
        StoryStepEntityResponse(
            id=e["id"],
            entity_key=e["entity_key"],
            value=e.get("value"),
            role=e.get("role"),
            group=e.get("group"),
        )
        for e in entities
    ]


@router.delete(
    "/story-step-entities/{entity_id}",
    status_code=204,
)
def delete_story_step_entity_api(
    entity_id: str,
    db: Session = Depends(get_db),
):
    """Delete an entity annotation from a story step."""
    delete_story_step_entity(db, entity_id)
    return None


