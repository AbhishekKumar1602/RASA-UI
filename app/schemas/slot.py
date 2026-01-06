from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Dict, Any, Literal


SlotType = Literal["text", "bool", "float", "list", "categorical", "any"]
SlotMappingType = Literal["from_entity", "from_text", "from_intent", "from_trigger_intent", "custom"]


class SlotCreate(BaseModel):
    """Schema for creating a new slot."""
    name: str
    slot_type: SlotType
    influence_conversation: bool = True
    initial_value: Optional[str] = None
    values: Optional[List[str]] = None  # For categorical slots
    min_value: Optional[float] = None  # For float slots
    max_value: Optional[float] = None  # For float slots


class SlotUpdate(BaseModel):
    """Schema for updating an existing slot."""
    name: Optional[str] = None
    slot_type: Optional[SlotType] = None
    influence_conversation: Optional[bool] = None
    initial_value: Optional[str] = None
    values: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class SlotResponse(BaseModel):
    """Schema for slot response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    name: str
    slot_type: str
    influence_conversation: bool
    initial_value: Optional[str] = None
    values: Optional[List[str]] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None


class SlotMappingCondition(BaseModel):
    """
    Schema for a single condition in slot mapping.
    
    Example:
    - {"active_loop": "request_form"}
    - {"active_loop": "outage_form"}
    """
    active_loop: Optional[str] = None
    requested_slot: Optional[str] = None


class SlotMappingCreate(BaseModel):
    """
    Schema for creating a slot mapping.
    
    Example mappings:
    1. from_entity:
       {"mapping_type": "from_entity", "entity_key": "account_number"}
    
    2. from_text with conditions:
       {"mapping_type": "from_text", "conditions": [{"active_loop": "request_form"}]}
    
    3. from_intent with value:
       {"mapping_type": "from_intent", "intent": "request_duplicate_bill", "value": "duplicate_bill"}
    """
    mapping_type: SlotMappingType
    entity_key: Optional[str] = None
    role: Optional[str] = None
    group: Optional[str] = None
    intent: Optional[str] = None
    not_intent: Optional[str] = None
    value: Optional[str] = None  # Value to set (for from_intent)
    conditions: Optional[List[Dict[str, Any]]] = None  # Multiple conditions
    active_loop: Optional[str] = None  # Legacy single condition (deprecated)
    priority: int = 0


class SlotMappingUpdate(BaseModel):
    """Schema for updating a slot mapping."""
    mapping_type: Optional[SlotMappingType] = None
    entity_key: Optional[str] = None
    role: Optional[str] = None
    group: Optional[str] = None
    intent: Optional[str] = None
    not_intent: Optional[str] = None
    value: Optional[str] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    active_loop: Optional[str] = None
    priority: Optional[int] = None


class SlotMappingResponse(BaseModel):
    """Schema for slot mapping response."""
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    mapping_type: str
    entity_key: Optional[str] = None
    role: Optional[str] = None
    group: Optional[str] = None
    intent: Optional[str] = None
    not_intent: Optional[str] = None
    value: Optional[str] = None
    conditions: Optional[List[Dict[str, Any]]] = None
    active_loop: Optional[str] = None  # Legacy field
    priority: int

