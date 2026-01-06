from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.rule import (
    RuleCreate,
    RuleResponse,
    RuleUpdate,
    RuleStepCreate,
    RuleStepResponse,
    RuleStepUpdate,
    RuleSlotEventCreate,
    RuleSlotEventResponse,
    RuleConditionCreate,
    RuleConditionResponse,
    RuleConditionUpdate,
    RuleStepEntityCreate,
    RuleStepEntityResponse,
)
from app.services.rule_service import (
    create_rule,
    list_rules,
    get_rule,
    update_rule,
    delete_rule,
    add_rule_step,
    list_rule_steps,
    update_rule_step,
    delete_rule_step,
    add_rule_slot_event,
    delete_rule_slot_event,
    add_rule_condition,
    list_rule_conditions,
    update_rule_condition,
    delete_rule_condition,
    add_rule_step_entity,
    list_rule_step_entities,
    delete_rule_step_entity,
)


router = APIRouter(prefix="/projects", tags=["Rules"])


# -------------------------------------------------
# RULE CRUD
# -------------------------------------------------

@router.post(
    "/{project_code}/versions/draft/rules",
    response_model=RuleResponse,
    status_code=201,
)
def create_rule_api(
    project_code: str,
    payload: RuleCreate,
    db: Session = Depends(get_db),
):
    """Create a new rule in the draft version."""
    return create_rule(db, project_code, payload)


@router.get(
    "/{project_code}/versions/{status}/rules",
    response_model=List[RuleResponse],
)
def list_rules_api(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    """List all rules for a version."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    rules = list_rules(db, project_code, status)
    return [RuleResponse(id=r.id, name=r.name) for r in rules]


@router.get(
    "/{project_code}/versions/{status}/rules/{rule_name}",
    response_model=RuleResponse,
)
def get_rule_api(
    project_code: str,
    status: str,
    rule_name: str,
    db: Session = Depends(get_db),
):
    """Get a specific rule."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_rule(db, project_code, status, rule_name)


@router.put(
    "/{project_code}/versions/draft/rules/{rule_name}",
    response_model=RuleResponse,
)
def update_rule_api(
    project_code: str,
    rule_name: str,
    payload: RuleUpdate,
    db: Session = Depends(get_db),
):
    """Update a rule in the draft version."""
    return update_rule(db, project_code, rule_name, payload)


@router.delete(
    "/{project_code}/versions/draft/rules/{rule_name}",
    status_code=204,
)
def delete_rule_api(
    project_code: str,
    rule_name: str,
    db: Session = Depends(get_db),
):
    """Delete a rule from the draft version."""
    delete_rule(db, project_code, rule_name)
    return None


# -------------------------------------------------
# RULE CONDITIONS
# -------------------------------------------------

@router.post(
    "/rules/{rule_id}/conditions",
    response_model=RuleConditionResponse,
    status_code=201,
)
def add_rule_condition_api(
    rule_id: str,
    payload: RuleConditionCreate,
    db: Session = Depends(get_db),
):
    """Add a condition to a rule."""
    return add_rule_condition(db, rule_id, payload)


@router.get(
    "/rules/{rule_id}/conditions",
    response_model=List[RuleConditionResponse],
)
def list_rule_conditions_api(
    rule_id: str,
    db: Session = Depends(get_db),
):
    """List all conditions for a rule."""
    return list_rule_conditions(db, rule_id)


@router.put(
    "/rule-conditions/{condition_id}",
    response_model=RuleConditionResponse,
)
def update_rule_condition_api(
    condition_id: str,
    payload: RuleConditionUpdate,
    db: Session = Depends(get_db),
):
    """Update a rule condition."""
    return update_rule_condition(db, condition_id, payload)


@router.delete(
    "/rule-conditions/{condition_id}",
    status_code=204,
)
def delete_rule_condition_api(
    condition_id: str,
    db: Session = Depends(get_db),
):
    """Delete a rule condition."""
    delete_rule_condition(db, condition_id)
    return None


# -------------------------------------------------
# RULE STEPS
# -------------------------------------------------

@router.post(
    "/rules/{rule_id}/steps",
    response_model=RuleStepResponse,
    status_code=201,
)
def add_rule_step_api(
    rule_id: str,
    payload: RuleStepCreate,
    db: Session = Depends(get_db),
):
    """
    Add a step to a rule.
    
    For action steps, provide ONE of:
    - action_name: Custom action (e.g., "action_save_to_db")
    - response_name: Utterance (e.g., "utter_greet")
    - form_name: Form activation (e.g., "request_form")
    
    For intent steps with entities:
    ```json
    {
        "step_type": "intent",
        "intent_name": "inform",
        "step_order": 0,
        "entities": [
            {"entity_key": "email", "value": "user@test.com"}
        ]
    }
    ```
    """
    step = add_rule_step(db, rule_id, payload)
    
    # Build entity response
    entities = []
    if hasattr(step, 'entities') and step.entities:
        entities = [
            RuleStepEntityResponse(
                id=e.id,
                entity_key=e.entity.entity_key,
                value=e.value,
                role=e.role,
                group=e.group,
            )
            for e in step.entities
        ]
    
    return RuleStepResponse(
        id=step.id,
        step_type=step.step_type,
        step_order=step.step_order,
        intent_name=step.intent.intent_name if step.intent else None,
        action_name=step.action.name if step.action else None,
        response_name=step.response.name if step.response else None,
        form_name=step.form.name if step.form else None,
        active_loop_value=step.active_loop_value,
        entities=entities,
    )


@router.get(
    "/rules/{rule_id}/steps",
    response_model=List[RuleStepResponse],
)
def list_rule_steps_api(
    rule_id: str,
    db: Session = Depends(get_db),
):
    """List all steps for a rule."""
    steps = list_rule_steps(db, rule_id)
    return [
        RuleStepResponse(
            id=s["id"],
            step_type=s["step_type"],
            step_order=s["step_order"],
            intent_name=s.get("intent_name"),
            action_name=s.get("action_name"),
            response_name=s.get("response_name"),
            form_name=s.get("form_name"),
            active_loop_value=s.get("active_loop_value"),
            entities=[
                RuleStepEntityResponse(
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
    "/rule-steps/{step_id}",
    response_model=RuleStepResponse,
)
def update_rule_step_api(
    step_id: str,
    payload: RuleStepUpdate,
    db: Session = Depends(get_db),
):
    """Update a rule step."""
    result = update_rule_step(db, step_id, payload)
    return RuleStepResponse(
        id=result["id"],
        step_type=result["step_type"],
        step_order=result["step_order"],
        intent_name=result.get("intent_name"),
        action_name=result.get("action_name"),
        response_name=result.get("response_name"),
        form_name=result.get("form_name"),
        active_loop_value=result.get("active_loop_value"),
    )


@router.delete(
    "/rule-steps/{step_id}",
    status_code=204,
)
def delete_rule_step_api(
    step_id: str,
    db: Session = Depends(get_db),
):
    """Delete a rule step."""
    delete_rule_step(db, step_id)
    return None


# -------------------------------------------------
# RULE SLOT EVENTS
# -------------------------------------------------

@router.post(
    "/rule-steps/{step_id}/slot-events",
    response_model=RuleSlotEventResponse,
    status_code=201,
)
def add_rule_slot_event_api(
    step_id: str,
    payload: RuleSlotEventCreate,
    db: Session = Depends(get_db),
):
    """Add a slot event to a rule step."""
    event = add_rule_slot_event(db, step_id, payload)
    return RuleSlotEventResponse(
        id=event.id,
        slot_name=event.slot.name,
        value=event.value,
    )


@router.delete(
    "/rule-slot-events/{event_id}",
    status_code=204,
)
def delete_rule_slot_event_api(
    event_id: str,
    db: Session = Depends(get_db),
):
    """Delete a rule slot event."""
    delete_rule_slot_event(db, event_id)
    return None


# -------------------------------------------------
# RULE STEP ENTITIES (NEW)
# -------------------------------------------------

@router.post(
    "/rule-steps/{step_id}/entities",
    response_model=RuleStepEntityResponse,
    status_code=201,
)
def add_rule_step_entity_api(
    step_id: str,
    payload: RuleStepEntityCreate,
    db: Session = Depends(get_db),
):
    """
    Add an entity annotation to a rule step.
    
    Only allowed for intent steps.
    
    Example:
    ```json
    {
        "entity_key": "email",
        "value": "user@test.com"
    }
    ```
    
    This generates RASA YAML:
    ```yaml
    - intent: inform
      entities:
        - email: user@test.com
    ```
    """
    result = add_rule_step_entity(db, step_id, payload)
    return RuleStepEntityResponse(
        id=result["id"],
        entity_key=result["entity_key"],
        value=result.get("value"),
        role=result.get("role"),
        group=result.get("group"),
    )


@router.get(
    "/rule-steps/{step_id}/entities",
    response_model=List[RuleStepEntityResponse],
)
def list_rule_step_entities_api(
    step_id: str,
    db: Session = Depends(get_db),
):
    """List all entity annotations for a rule step."""
    entities = list_rule_step_entities(db, step_id)
    return [
        RuleStepEntityResponse(
            id=e["id"],
            entity_key=e["entity_key"],
            value=e.get("value"),
            role=e.get("role"),
            group=e.get("group"),
        )
        for e in entities
    ]


@router.delete(
    "/rule-step-entities/{entity_id}",
    status_code=204,
)
def delete_rule_step_entity_api(
    entity_id: str,
    db: Session = Depends(get_db),
):
    """Delete an entity annotation from a rule step."""
    delete_rule_step_entity(db, entity_id)
    return None
