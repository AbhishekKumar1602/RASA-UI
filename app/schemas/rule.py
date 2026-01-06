from pydantic import BaseModel, ConfigDict
from typing import Optional, Literal, List


class RuleCreate(BaseModel):
    """Schema for creating a new rule."""
    name: str


class RuleUpdate(BaseModel):
    """Schema for updating an existing rule."""
    name: Optional[str] = None


class RuleResponse(BaseModel):
    """Schema for rule response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str


# -------------------------------------------------
# RULE STEP ENTITY SCHEMAS (NEW)
# -------------------------------------------------

class RuleStepEntityCreate(BaseModel):
    """
    Schema for adding an entity annotation to an intent step.
    
    Example:
    ```json
    {
        "entity_key": "email",
        "value": "user@test.com",
        "role": null,
        "group": null
    }
    ```
    """
    entity_key: str
    value: Optional[str] = None
    role: Optional[str] = None
    group: Optional[str] = None


class RuleStepEntityResponse(BaseModel):
    """Schema for rule step entity response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    entity_key: str
    value: Optional[str] = None
    role: Optional[str] = None
    group: Optional[str] = None


# -------------------------------------------------
# RULE STEP SCHEMAS
# -------------------------------------------------

class RuleStepCreate(BaseModel):
    """
    Schema for creating a rule step.
    
    For action steps, provide ONE of:
    - action_name: Custom action (e.g., "action_save_to_db")
    - response_name: Utterance (e.g., "utter_greet")
    - form_name: Form activation (e.g., "request_form")
    
    For intent steps with entities, provide entities list.
    
    Examples:
    
    1. Simple intent step:
    ```json
    {"step_type": "intent", "intent_name": "greet", "step_order": 0}
    ```
    
    2. Intent step with entities:
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
    
    3. Response utterance:
    ```json
    {"step_type": "action", "response_name": "utter_greet", "step_order": 1}
    ```
    
    4. Custom action:
    ```json
    {"step_type": "action", "action_name": "action_save_to_db", "step_order": 2}
    ```
    
    5. Form activation:
    ```json
    {"step_type": "action", "form_name": "request_form", "step_order": 1}
    ```
    
    6. Active loop:
    ```json
    {"step_type": "active_loop", "active_loop_value": "request_form", "step_order": 2}
    ```
    
    7. Deactivate loop:
    ```json
    {"step_type": "active_loop", "active_loop_value": null, "step_order": 3}
    ```
    """
    step_type: Literal["intent", "action", "active_loop", "slot"]
    intent_name: Optional[str] = None
    action_name: Optional[str] = None  # For action_* custom actions
    response_name: Optional[str] = None  # For utter_* responses
    form_name: Optional[str] = None  # For form activation
    active_loop_value: Optional[str] = None
    step_order: int
    
    # NEW: Entity annotations for intent steps
    entities: Optional[List[RuleStepEntityCreate]] = None


class RuleStepUpdate(BaseModel):
    """Schema for updating a rule step."""
    step_type: Optional[Literal["intent", "action", "active_loop", "slot"]] = None
    intent_name: Optional[str] = None
    action_name: Optional[str] = None
    response_name: Optional[str] = None
    form_name: Optional[str] = None
    active_loop_value: Optional[str] = None
    step_order: Optional[int] = None


class RuleStepResponse(BaseModel):
    """Schema for rule step response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    step_type: str
    step_order: int
    intent_name: Optional[str] = None
    action_name: Optional[str] = None
    response_name: Optional[str] = None
    form_name: Optional[str] = None
    active_loop_value: Optional[str] = None
    entities: Optional[List[RuleStepEntityResponse]] = None  # NEW


# -------------------------------------------------
# RULE SLOT EVENT SCHEMAS
# -------------------------------------------------

class RuleSlotEventCreate(BaseModel):
    """Schema for creating a slot event in a rule step."""
    slot_name: str
    value: Optional[str] = None


class RuleSlotEventResponse(BaseModel):
    """Schema for rule slot event response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    slot_name: str
    value: Optional[str] = None


# -------------------------------------------------
# RULE CONDITION SCHEMAS
# -------------------------------------------------

class RuleConditionCreate(BaseModel):
    """
    Schema for creating a rule condition.
    
    Examples:
    
    1. Slot condition:
    ```json
    {"condition_type": "slot", "slot_name": "request_type", "slot_value": "duplicate_bill"}
    ```
    
    2. Active loop condition:
    ```json
    {"condition_type": "active_loop", "active_loop": "request_form"}
    ```
    """
    condition_type: Literal["slot", "active_loop"]
    slot_name: Optional[str] = None
    slot_value: Optional[str] = None
    active_loop: Optional[str] = None
    order_index: int = 0


class RuleConditionUpdate(BaseModel):
    """Schema for updating a rule condition."""
    condition_type: Optional[Literal["slot", "active_loop"]] = None
    slot_name: Optional[str] = None
    slot_value: Optional[str] = None
    active_loop: Optional[str] = None
    order_index: Optional[int] = None


class RuleConditionResponse(BaseModel):
    """Schema for rule condition response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    condition_type: str
    slot_name: Optional[str] = None
    slot_value: Optional[str] = None
    active_loop: Optional[str] = None
    order_index: int

