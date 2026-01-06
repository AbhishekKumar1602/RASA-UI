import uuid
from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models import (
    Story,
    StoryStep,
    StorySlotEvent,
    Intent,
    Action,
    Response,
    Slot,
    Form,
    Entity,
)
from app.models.story import StoryStepEntity
from app.services.common import get_version_by_status, get_draft_version


def create_story(db: Session, project_code: str, payload):
    """Create a new story in the draft version."""
    version = get_draft_version(db, project_code)

    existing = (
        db.query(Story)
        .filter(
            Story.version_id == version.id,
            Story.name == payload.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Story already exists in draft version")

    story = Story(
        name=payload.name,
        version_id=version.id,
    )
    db.add(story)
    db.commit()
    db.refresh(story)
    return story


def list_stories(db: Session, project_code: str, status: str):
    """List all stories for a version."""
    version = get_version_by_status(db, project_code, status)

    return (
        db.query(Story)
        .filter(Story.version_id == version.id)
        .order_by(Story.name)
        .all()
    )


def get_story(db: Session, project_code: str, status: str, story_name: str):
    """Get a specific story by name."""
    version = get_version_by_status(db, project_code, status)

    story = (
        db.query(Story)
        .filter(
            Story.version_id == version.id,
            Story.name == story_name,
        )
        .first()
    )
    if not story:
        raise HTTPException(404, "Story not found")

    return story


def update_story(db: Session, project_code: str, story_name: str, payload):
    """Update a story in the draft version."""
    version = get_draft_version(db, project_code)

    story = (
        db.query(Story)
        .filter(
            Story.version_id == version.id,
            Story.name == story_name,
        )
        .first()
    )
    if not story:
        raise HTTPException(404, "Story not found")

    if payload.name and payload.name != story_name:
        existing = (
            db.query(Story)
            .filter(
                Story.version_id == version.id,
                Story.name == payload.name,
            )
            .first()
        )
        if existing:
            raise HTTPException(400, "Story with this name already exists")
        story.name = payload.name

    db.commit()
    db.refresh(story)
    return story


def delete_story(db: Session, project_code: str, story_name: str):
    """Delete a story from the draft version."""
    version = get_draft_version(db, project_code)

    story = (
        db.query(Story)
        .filter(
            Story.version_id == version.id,
            Story.name == story_name,
        )
        .first()
    )
    if not story:
        raise HTTPException(404, "Story not found")

    # Delete all related data
    steps = db.query(StoryStep).filter(StoryStep.story_id == story.id).all()
    for step in steps:
        db.query(StorySlotEvent).filter(
            StorySlotEvent.story_step_id == step.id
        ).delete()
        db.query(StoryStepEntity).filter(
            StoryStepEntity.story_step_id == step.id
        ).delete()

    db.query(StoryStep).filter(StoryStep.story_id == story.id).delete()
    db.delete(story)
    db.commit()


# -------------------------------------------------
# STORY STEPS
# -------------------------------------------------


def add_story_step(db: Session, story_id: str, payload):
    """
    Add a step to a story.

    Supports:
    - Intent steps with optional entity annotations
    - Action steps (custom action, response utterance, or form)
    - OR conditions with multiple intents
    - Active loop control
    - Checkpoints
    """
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(404, "Story not found")

    # Handle OR condition
    if payload.step_type == "or":
        return _create_or_group(db, story, payload)

    # Validate action step - must have exactly one of action_name, response_name, or form_name
    if payload.step_type == "action":
        provided = sum(
            [
                bool(payload.action_name),
                bool(payload.response_name),
                bool(payload.form_name),
            ]
        )
        if provided == 0:
            raise HTTPException(
                400,
                "action_name, response_name, or form_name is required for action step",
            )
        if provided > 1:
            raise HTTPException(
                400, "Provide only one of action_name, response_name, or form_name"
            )

    step = StoryStep(
        story_id=story.id,
        step_type=payload.step_type,
        timeline_index=payload.timeline_index,
        step_order=payload.step_order,
        active_loop_value=payload.active_loop_value,
        checkpoint_name=getattr(payload, "checkpoint_name", None),
    )

    # Handle intent
    if payload.intent_name:
        intent = (
            db.query(Intent)
            .filter(
                Intent.intent_name == payload.intent_name,
                Intent.version_id == story.version_id,
            )
            .first()
        )
        if not intent:
            raise HTTPException(400, "Intent not found in same version")
        step.intent_id = intent.id

    # Handle custom action (action_*)
    if payload.action_name:
        action = (
            db.query(Action)
            .filter(
                Action.name == payload.action_name,
                Action.version_id == story.version_id,
            )
            .first()
        )
        if not action:
            raise HTTPException(
                400, f"Action '{payload.action_name}' not found in same version"
            )
        step.action_id = action.id

    # Handle response (utter_*)
    if payload.response_name:
        response = (
            db.query(Response)
            .filter(
                Response.name == payload.response_name,
                Response.version_id == story.version_id,
            )
            .first()
        )
        if not response:
            raise HTTPException(
                400, f"Response '{payload.response_name}' not found in same version"
            )
        step.response_id = response.id

    # Handle form
    if payload.form_name:
        form = (
            db.query(Form)
            .filter(
                Form.name == payload.form_name,
                Form.version_id == story.version_id,
            )
            .first()
        )
        if not form:
            raise HTTPException(
                400, f"Form '{payload.form_name}' not found in same version"
            )
        step.form_id = form.id

    db.add(step)
    db.flush()

    # Handle entity annotations for intent steps (NEW)
    if payload.step_type == "intent" and payload.entities:
        for entity_data in payload.entities:
            entity = (
                db.query(Entity)
                .filter(
                    Entity.entity_key == entity_data.entity_key,
                    Entity.version_id == story.version_id,
                )
                .first()
            )
            if not entity:
                raise HTTPException(
                    400, f"Entity '{entity_data.entity_key}' not found in same version"
                )

            step_entity = StoryStepEntity(
                story_step_id=step.id,
                entity_id=entity.id,
                value=entity_data.value,
                role=entity_data.role,
                group=entity_data.group,
            )
            db.add(step_entity)

    db.commit()
    db.refresh(step)
    return step


def _create_or_group(db: Session, story: Story, payload):
    """
    Create an OR condition group with multiple intents.

    Creates multiple steps with the same or_group_id.
    """
    if not payload.or_intents or len(payload.or_intents) < 2:
        raise HTTPException(400, "OR condition requires at least 2 intents")

    # Generate a unique group ID
    or_group_id = str(uuid.uuid4())

    created_steps = []

    for idx, intent_name in enumerate(payload.or_intents):
        intent = (
            db.query(Intent)
            .filter(
                Intent.intent_name == intent_name,
                Intent.version_id == story.version_id,
            )
            .first()
        )
        if not intent:
            raise HTTPException(
                400, f"Intent '{intent_name}' not found in same version"
            )

        step = StoryStep(
            story_id=story.id,
            step_type="or",
            timeline_index=payload.timeline_index,
            step_order=payload.step_order,
            intent_id=intent.id,
            or_group_id=or_group_id,
        )
        db.add(step)
        created_steps.append(step)

    db.commit()

    # Refresh and return the first step (representative)
    if created_steps:
        db.refresh(created_steps[0])
        return created_steps[0]


def list_story_steps(db: Session, story_id: str):
    """List all steps for a story."""
    story = db.query(Story).filter(Story.id == story_id).first()
    if not story:
        raise HTTPException(404, "Story not found")

    steps = (
        db.query(StoryStep)
        .options(
            joinedload(StoryStep.intent),
            joinedload(StoryStep.action),
            joinedload(StoryStep.response),
            joinedload(StoryStep.form),
            joinedload(StoryStep.entities).joinedload(StoryStepEntity.entity),
        )
        .filter(StoryStep.story_id == story_id)
        .order_by(StoryStep.timeline_index, StoryStep.step_order)
        .all()
    )

    return [
        {
            "id": step.id,
            "step_type": step.step_type,
            "timeline_index": step.timeline_index,
            "step_order": step.step_order,
            "intent_name": step.intent.intent_name if step.intent else None,
            "action_name": step.action.name if step.action else None,
            "response_name": step.response.name if step.response else None,
            "form_name": step.form.name if step.form else None,
            "active_loop_value": step.active_loop_value,
            "checkpoint_name": step.checkpoint_name,
            "or_group_id": step.or_group_id,
            "entities": (
                [
                    {
                        "id": e.id,
                        "entity_key": e.entity.entity_key,
                        "value": e.value,
                        "role": e.role,
                        "group": e.group,
                    }
                    for e in step.entities
                ]
                if step.entities
                else []
            ),
        }
        for step in steps
    ]


def update_story_step(db: Session, step_id: str, payload):
    """Update a story step."""
    step = (
        db.query(StoryStep)
        .options(joinedload(StoryStep.story))
        .filter(StoryStep.id == step_id)
        .first()
    )
    if not step:
        raise HTTPException(404, "Story step not found")

    if payload.step_type is not None:
        step.step_type = payload.step_type
    if payload.timeline_index is not None:
        step.timeline_index = payload.timeline_index
    if payload.step_order is not None:
        step.step_order = payload.step_order
    if payload.active_loop_value is not None:
        step.active_loop_value = payload.active_loop_value
    if hasattr(payload, "checkpoint_name") and payload.checkpoint_name is not None:
        step.checkpoint_name = payload.checkpoint_name

    # Handle intent
    if payload.intent_name is not None:
        if payload.intent_name:
            intent = (
                db.query(Intent)
                .filter(
                    Intent.intent_name == payload.intent_name,
                    Intent.version_id == step.story.version_id,
                )
                .first()
            )
            if not intent:
                raise HTTPException(400, "Intent not found in same version")
            step.intent_id = intent.id
        else:
            step.intent_id = None

    # Handle action
    if payload.action_name is not None:
        if payload.action_name:
            action = (
                db.query(Action)
                .filter(
                    Action.name == payload.action_name,
                    Action.version_id == step.story.version_id,
                )
                .first()
            )
            if not action:
                raise HTTPException(400, "Action not found in same version")
            step.action_id = action.id
        else:
            step.action_id = None

    # Handle response
    if payload.response_name is not None:
        if payload.response_name:
            response = (
                db.query(Response)
                .filter(
                    Response.name == payload.response_name,
                    Response.version_id == step.story.version_id,
                )
                .first()
            )
            if not response:
                raise HTTPException(400, "Response not found in same version")
            step.response_id = response.id
        else:
            step.response_id = None

    # Handle form
    if payload.form_name is not None:
        if payload.form_name:
            form = (
                db.query(Form)
                .filter(
                    Form.name == payload.form_name,
                    Form.version_id == step.story.version_id,
                )
                .first()
            )
            if not form:
                raise HTTPException(400, "Form not found in same version")
            step.form_id = form.id
        else:
            step.form_id = None

    db.commit()
    db.refresh(step)

    return {
        "id": step.id,
        "step_type": step.step_type,
        "timeline_index": step.timeline_index,
        "step_order": step.step_order,
        "intent_name": step.intent.intent_name if step.intent else None,
        "action_name": step.action.name if step.action else None,
        "response_name": step.response.name if step.response else None,
        "form_name": step.form.name if step.form else None,
        "active_loop_value": step.active_loop_value,
        "checkpoint_name": step.checkpoint_name,
        "or_group_id": step.or_group_id,
    }


def delete_story_step(db: Session, step_id: str):
    """Delete a story step."""
    step = db.query(StoryStep).filter(StoryStep.id == step_id).first()
    if not step:
        raise HTTPException(404, "Story step not found")

    # Delete related data
    db.query(StorySlotEvent).filter(StorySlotEvent.story_step_id == step.id).delete()
    db.query(StoryStepEntity).filter(StoryStepEntity.story_step_id == step.id).delete()

    # If this is part of an OR group, delete all steps in the group
    if step.or_group_id:
        or_steps = (
            db.query(StoryStep).filter(StoryStep.or_group_id == step.or_group_id).all()
        )
        for or_step in or_steps:
            db.query(StorySlotEvent).filter(
                StorySlotEvent.story_step_id == or_step.id
            ).delete()
            db.query(StoryStepEntity).filter(
                StoryStepEntity.story_step_id == or_step.id
            ).delete()
            db.delete(or_step)
    else:
        db.delete(step)

    db.commit()


# -------------------------------------------------
# STORY SLOT EVENTS
# -------------------------------------------------


def add_story_slot_event(db: Session, step_id: str, payload):
    """Add a slot event to a story step."""
    step = (
        db.query(StoryStep)
        .options(joinedload(StoryStep.story))
        .filter(StoryStep.id == step_id)
        .first()
    )
    if not step:
        raise HTTPException(404, "Story step not found")

    slot = (
        db.query(Slot)
        .filter(
            Slot.name == payload.slot_name,
            Slot.version_id == step.story.version_id,
        )
        .first()
    )
    if not slot:
        raise HTTPException(400, "Slot not found in same version")

    event = StorySlotEvent(
        story_step_id=step.id,
        slot_id=slot.id,
        value=payload.value,
    )

    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def delete_story_slot_event(db: Session, event_id: str):
    """Delete a story slot event."""
    event = db.query(StorySlotEvent).filter(StorySlotEvent.id == event_id).first()
    if not event:
        raise HTTPException(404, "Story slot event not found")

    db.delete(event)
    db.commit()


# -------------------------------------------------
# STORY STEP ENTITIES (NEW)
# -------------------------------------------------


def add_story_step_entity(db: Session, step_id: str, payload):
    """Add an entity annotation to a story step."""
    step = (
        db.query(StoryStep)
        .options(joinedload(StoryStep.story))
        .filter(StoryStep.id == step_id)
        .first()
    )
    if not step:
        raise HTTPException(404, "Story step not found")

    if step.step_type != "intent":
        raise HTTPException(400, "Entity annotations are only allowed for intent steps")

    entity = (
        db.query(Entity)
        .filter(
            Entity.entity_key == payload.entity_key,
            Entity.version_id == step.story.version_id,
        )
        .first()
    )
    if not entity:
        raise HTTPException(
            400, f"Entity '{payload.entity_key}' not found in same version"
        )

    step_entity = StoryStepEntity(
        story_step_id=step.id,
        entity_id=entity.id,
        value=payload.value,
        role=payload.role,
        group=payload.group,
    )
    db.add(step_entity)
    db.commit()
    db.refresh(step_entity)

    return {
        "id": step_entity.id,
        "entity_key": entity.entity_key,
        "value": step_entity.value,
        "role": step_entity.role,
        "group": step_entity.group,
    }


def list_story_step_entities(db: Session, step_id: str):
    """List all entity annotations for a story step."""
    step = db.query(StoryStep).filter(StoryStep.id == step_id).first()
    if not step:
        raise HTTPException(404, "Story step not found")

    entities = (
        db.query(StoryStepEntity)
        .options(joinedload(StoryStepEntity.entity))
        .filter(StoryStepEntity.story_step_id == step_id)
        .all()
    )

    return [
        {
            "id": e.id,
            "entity_key": e.entity.entity_key,
            "value": e.value,
            "role": e.role,
            "group": e.group,
        }
        for e in entities
    ]


def delete_story_step_entity(db: Session, entity_id: str):
    """Delete an entity annotation from a story step."""
    entity = db.query(StoryStepEntity).filter(StoryStepEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(404, "Story step entity not found")

    db.delete(entity)
    db.commit()
