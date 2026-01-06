from pydantic import BaseModel, ConfigDict, Field
from typing import Optional, Literal, List


class StoryCreate(BaseModel):
    """Schema for creating a new story."""
    name: str


class StoryUpdate(BaseModel):
    """Schema for updating an existing story."""
    name: Optional[str] = None


class StoryResponse(BaseModel):
    """Schema for story response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str


# -------------------------------------------------
# STORY STEP ENTITY SCHEMAS (NEW)
# -------------------------------------------------

class StoryStepEntityCreate(BaseModel):
    entity_key: str
    value: Optional[str] = None
    role: Optional[str] = None
    group: Optional[str] = None


class StoryStepEntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    entity_key: str
    value: Optional[str] = None
    role: Optional[str] = None
    group: Optional[str] = None


# -------------------------------------------------
# STORY STEP SCHEMAS
# -------------------------------------------------

class StoryStepCreate(BaseModel):

    step_type: Literal["intent", "action", "slot", "active_loop", "checkpoint", "or"]
    intent_name: Optional[str] = None
    action_name: Optional[str] = None  # For action_* custom actions
    response_name: Optional[str] = None  # For utter_* responses
    form_name: Optional[str] = None  # For form activation
    active_loop_value: Optional[str] = None
    checkpoint_name: Optional[str] = None
    timeline_index: int
    step_order: int
    
    # NEW: Entity annotations for intent steps
    entities: Optional[List[StoryStepEntityCreate]] = None
    
    # NEW: For OR conditions - list of intent names
    or_intents: Optional[List[str]] = None


class StoryStepUpdate(BaseModel):
    """Schema for updating a story step."""
    step_type: Optional[Literal["intent", "action", "slot", "active_loop", "checkpoint", "or"]] = None
    intent_name: Optional[str] = None
    action_name: Optional[str] = None
    response_name: Optional[str] = None
    form_name: Optional[str] = None
    active_loop_value: Optional[str] = None
    checkpoint_name: Optional[str] = None
    timeline_index: Optional[int] = None
    step_order: Optional[int] = None


class StoryStepResponse(BaseModel):
    """Schema for story step response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    step_type: str
    timeline_index: int
    step_order: int
    intent_name: Optional[str] = None
    action_name: Optional[str] = None
    response_name: Optional[str] = None
    form_name: Optional[str] = None
    active_loop_value: Optional[str] = None
    checkpoint_name: Optional[str] = None
    or_group_id: Optional[str] = None  # NEW
    entities: Optional[List[StoryStepEntityResponse]] = None  # NEW

class StorySlotEventCreate(BaseModel):
    slot_name: str
    value: Optional[str] = None


class StorySlotEventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    slot_name: str
    value: Optional[str] = None

class OrGroupCreate(BaseModel):
    intent_names: List[str] = Field(..., min_length=2, description="At least 2 intents required for OR")
    timeline_index: int
    step_order: int


class OrGroupResponse(BaseModel):
    or_group_id: str
    intent_names: List[str]
    timeline_index: int
    step_order: int
