from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException

from app.models import (
    Rule,
    RuleStep,
    RuleSlotEvent,
    RuleCondition,
    Intent,
    Action,
    Response,
    Slot,
    Form,
    Entity,
)
from app.models.rule import RuleStepEntity
from app.services.common import get_version_by_status, get_draft_version


def create_rule(db: Session, project_code: str, payload):
    """Create a new rule in the draft version."""
    version = get_draft_version(db, project_code)

    existing = (
        db.query(Rule)
        .filter(
            Rule.version_id == version.id,
            Rule.name == payload.name,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Rule already exists in draft version")

    rule = Rule(
        name=payload.name,
        version_id=version.id,
    )
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


def list_rules(db: Session, project_code: str, status: str):
    """List all rules for a version."""
    version = get_version_by_status(db, project_code, status)

    return (
        db.query(Rule).filter(Rule.version_id == version.id).order_by(Rule.name).all()
    )


def get_rule(db: Session, project_code: str, status: str, rule_name: str):
    """Get a specific rule by name."""
    version = get_version_by_status(db, project_code, status)

    rule = (
        db.query(Rule)
        .filter(
            Rule.version_id == version.id,
            Rule.name == rule_name,
        )
        .first()
    )
    if not rule:
        raise HTTPException(404, "Rule not found")

    return rule


def update_rule(db: Session, project_code: str, rule_name: str, payload):
    """Update a rule in the draft version."""
    version = get_draft_version(db, project_code)

    rule = (
        db.query(Rule)
        .filter(
            Rule.version_id == version.id,
            Rule.name == rule_name,
        )
        .first()
    )
    if not rule:
        raise HTTPException(404, "Rule not found")

    if payload.name and payload.name != rule_name:
        existing = (
            db.query(Rule)
            .filter(
                Rule.version_id == version.id,
                Rule.name == payload.name,
            )
            .first()
        )
        if existing:
            raise HTTPException(400, "Rule with this name already exists")
        rule.name = payload.name

    db.commit()
    db.refresh(rule)
    return rule


def delete_rule(db: Session, project_code: str, rule_name: str):
    """Delete a rule from the draft version."""
    version = get_draft_version(db, project_code)

    rule = (
        db.query(Rule)
        .filter(
            Rule.version_id == version.id,
            Rule.name == rule_name,
        )
        .first()
    )
    if not rule:
        raise HTTPException(404, "Rule not found")

    # Delete all related data
    steps = db.query(RuleStep).filter(RuleStep.rule_id == rule.id).all()
    for step in steps:
        db.query(RuleSlotEvent).filter(RuleSlotEvent.rule_step_id == step.id).delete()
        db.query(RuleStepEntity).filter(RuleStepEntity.rule_step_id == step.id).delete()

    db.query(RuleStep).filter(RuleStep.rule_id == rule.id).delete()
    db.query(RuleCondition).filter(RuleCondition.rule_id == rule.id).delete()

    db.delete(rule)
    db.commit()


# -------------------------------------------------
# RULE CONDITIONS
# -------------------------------------------------


def add_rule_condition(db: Session, rule_id: str, payload):
    """Add a condition to a rule."""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(404, "Rule not found")

    condition = RuleCondition(
        rule_id=rule.id,
        condition_type=payload.condition_type,
        slot_name=payload.slot_name,
        slot_value=payload.slot_value,
        active_loop=payload.active_loop,
        order_index=payload.order_index,
    )
    db.add(condition)
    db.commit()
    db.refresh(condition)
    return condition


def list_rule_conditions(db: Session, rule_id: str):
    """List all conditions for a rule."""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(404, "Rule not found")

    conditions = (
        db.query(RuleCondition)
        .filter(RuleCondition.rule_id == rule_id)
        .order_by(RuleCondition.order_index)
        .all()
    )

    return [
        {
            "id": c.id,
            "condition_type": c.condition_type,
            "slot_name": c.slot_name,
            "slot_value": c.slot_value,
            "active_loop": c.active_loop,
            "order_index": c.order_index,
        }
        for c in conditions
    ]


def update_rule_condition(db: Session, condition_id: str, payload):
    """Update a rule condition."""
    condition = db.query(RuleCondition).filter(RuleCondition.id == condition_id).first()
    if not condition:
        raise HTTPException(404, "Rule condition not found")

    if payload.condition_type is not None:
        condition.condition_type = payload.condition_type
    if payload.slot_name is not None:
        condition.slot_name = payload.slot_name
    if payload.slot_value is not None:
        condition.slot_value = payload.slot_value
    if payload.active_loop is not None:
        condition.active_loop = payload.active_loop
    if payload.order_index is not None:
        condition.order_index = payload.order_index

    db.commit()
    db.refresh(condition)
    return condition


def delete_rule_condition(db: Session, condition_id: str):
    """Delete a rule condition."""
    condition = db.query(RuleCondition).filter(RuleCondition.id == condition_id).first()
    if not condition:
        raise HTTPException(404, "Rule condition not found")

    db.delete(condition)
    db.commit()


# -------------------------------------------------
# RULE STEPS
# -------------------------------------------------


def add_rule_step(db: Session, rule_id: str, payload):
    """
    Add a step to a rule.

    Supports:
    - Intent steps with optional entity annotations
    - Action steps (custom action, response utterance, or form)
    - Active loop control
    - Slot events
    """
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(404, "Rule not found")

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

    step = RuleStep(
        rule_id=rule.id,
        step_type=payload.step_type,
        step_order=payload.step_order,
        active_loop_value=payload.active_loop_value,
    )

    # Handle intent
    if payload.intent_name:
        intent = (
            db.query(Intent)
            .filter(
                Intent.intent_name == payload.intent_name,
                Intent.version_id == rule.version_id,
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
                Action.version_id == rule.version_id,
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
                Response.version_id == rule.version_id,
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
                Form.version_id == rule.version_id,
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
                    Entity.version_id == rule.version_id,
                )
                .first()
            )
            if not entity:
                raise HTTPException(
                    400, f"Entity '{entity_data.entity_key}' not found in same version"
                )

            step_entity = RuleStepEntity(
                rule_step_id=step.id,
                entity_id=entity.id,
                value=entity_data.value,
                role=entity_data.role,
                group=entity_data.group,
            )
            db.add(step_entity)

    db.commit()
    db.refresh(step)
    return step


def list_rule_steps(db: Session, rule_id: str):
    """List all steps for a rule."""
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(404, "Rule not found")

    steps = (
        db.query(RuleStep)
        .options(
            joinedload(RuleStep.intent),
            joinedload(RuleStep.action),
            joinedload(RuleStep.response),
            joinedload(RuleStep.form),
            joinedload(RuleStep.entities).joinedload(RuleStepEntity.entity),
        )
        .filter(RuleStep.rule_id == rule_id)
        .order_by(RuleStep.step_order)
        .all()
    )

    return [
        {
            "id": step.id,
            "step_type": step.step_type,
            "step_order": step.step_order,
            "intent_name": step.intent.intent_name if step.intent else None,
            "action_name": step.action.name if step.action else None,
            "response_name": step.response.name if step.response else None,
            "form_name": step.form.name if step.form else None,
            "active_loop_value": step.active_loop_value,
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


def update_rule_step(db: Session, step_id: str, payload):
    """Update a rule step."""
    step = (
        db.query(RuleStep)
        .options(joinedload(RuleStep.rule))
        .filter(RuleStep.id == step_id)
        .first()
    )
    if not step:
        raise HTTPException(404, "Rule step not found")

    if payload.step_type is not None:
        step.step_type = payload.step_type
    if payload.step_order is not None:
        step.step_order = payload.step_order
    if payload.active_loop_value is not None:
        step.active_loop_value = payload.active_loop_value

    # Handle intent
    if payload.intent_name is not None:
        if payload.intent_name:
            intent = (
                db.query(Intent)
                .filter(
                    Intent.intent_name == payload.intent_name,
                    Intent.version_id == step.rule.version_id,
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
                    Action.version_id == step.rule.version_id,
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
                    Response.version_id == step.rule.version_id,
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
                    Form.version_id == step.rule.version_id,
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
        "step_order": step.step_order,
        "intent_name": step.intent.intent_name if step.intent else None,
        "action_name": step.action.name if step.action else None,
        "response_name": step.response.name if step.response else None,
        "form_name": step.form.name if step.form else None,
        "active_loop_value": step.active_loop_value,
    }


def delete_rule_step(db: Session, step_id: str):
    """Delete a rule step."""
    step = db.query(RuleStep).filter(RuleStep.id == step_id).first()
    if not step:
        raise HTTPException(404, "Rule step not found")

    # Delete related data
    db.query(RuleSlotEvent).filter(RuleSlotEvent.rule_step_id == step.id).delete()
    db.query(RuleStepEntity).filter(RuleStepEntity.rule_step_id == step.id).delete()

    db.delete(step)
    db.commit()


# -------------------------------------------------
# RULE SLOT EVENTS
# -------------------------------------------------


def add_rule_slot_event(db: Session, step_id: str, payload):
    """Add a slot event to a rule step."""
    step = (
        db.query(RuleStep)
        .options(joinedload(RuleStep.rule))
        .filter(RuleStep.id == step_id)
        .first()
    )
    if not step:
        raise HTTPException(404, "Rule step not found")

    slot = (
        db.query(Slot)
        .filter(
            Slot.name == payload.slot_name,
            Slot.version_id == step.rule.version_id,
        )
        .first()
    )
    if not slot:
        raise HTTPException(400, "Slot not found in same version")

    event = RuleSlotEvent(
        rule_step_id=step.id,
        slot_id=slot.id,
        value=payload.value,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event


def delete_rule_slot_event(db: Session, event_id: str):
    """Delete a rule slot event."""
    event = db.query(RuleSlotEvent).filter(RuleSlotEvent.id == event_id).first()
    if not event:
        raise HTTPException(404, "Rule slot event not found")

    db.delete(event)
    db.commit()


# -------------------------------------------------
# RULE STEP ENTITIES (NEW)
# -------------------------------------------------


def add_rule_step_entity(db: Session, step_id: str, payload):
    """Add an entity annotation to a rule step."""
    step = (
        db.query(RuleStep)
        .options(joinedload(RuleStep.rule))
        .filter(RuleStep.id == step_id)
        .first()
    )
    if not step:
        raise HTTPException(404, "Rule step not found")

    if step.step_type != "intent":
        raise HTTPException(400, "Entity annotations are only allowed for intent steps")

    entity = (
        db.query(Entity)
        .filter(
            Entity.entity_key == payload.entity_key,
            Entity.version_id == step.rule.version_id,
        )
        .first()
    )
    if not entity:
        raise HTTPException(
            400, f"Entity '{payload.entity_key}' not found in same version"
        )

    step_entity = RuleStepEntity(
        rule_step_id=step.id,
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


def list_rule_step_entities(db: Session, step_id: str):
    """List all entity annotations for a rule step."""
    step = db.query(RuleStep).filter(RuleStep.id == step_id).first()
    if not step:
        raise HTTPException(404, "Rule step not found")

    entities = (
        db.query(RuleStepEntity)
        .options(joinedload(RuleStepEntity.entity))
        .filter(RuleStepEntity.rule_step_id == step_id)
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


def delete_rule_step_entity(db: Session, entity_id: str):
    """Delete an entity annotation from a rule step."""
    entity = db.query(RuleStepEntity).filter(RuleStepEntity.id == entity_id).first()
    if not entity:
        raise HTTPException(404, "Rule step entity not found")

    db.delete(entity)
    db.commit()
