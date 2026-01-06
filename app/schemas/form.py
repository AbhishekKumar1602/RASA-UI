from pydantic import BaseModel, ConfigDict
from typing import List, Optional, Literal


class FormCreate(BaseModel):
    """Schema for creating a new form."""

    name: str
    ignored_intents: Optional[List[str]] = None


class FormUpdate(BaseModel):
    """Schema for updating an existing form."""

    name: Optional[str] = None
    ignored_intents: Optional[List[str]] = None


class FormResponse(BaseModel):
    """Schema for form response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    ignored_intents: Optional[List[str]] = None


class FormSlotMappingCreate(BaseModel):
    """
    Schema for creating a form slot mapping.

    Example mappings:
    1. from_entity:
       {"mapping_type": "from_entity", "entity_key": "account_number"}

    2. from_text:
       {"mapping_type": "from_text"}

    3. from_intent with value:
       {"mapping_type": "from_intent", "intent": "affirm", "value": "true"}
    """

    mapping_type: Literal[
        "from_entity", "from_text", "from_intent", "from_trigger_intent"
    ]
    entity_key: Optional[str] = None
    intent: Optional[str] = None
    not_intent: Optional[str] = None
    value: Optional[str] = None  # Value to set when intent matches


class FormSlotMappingResponse(BaseModel):
    """Schema for form slot mapping response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    mapping_type: str
    entity_key: Optional[str] = None
    intent: Optional[str] = None
    not_intent: Optional[str] = None
    value: Optional[str] = None


class FormRequiredSlotCreate(BaseModel):
    """Schema for adding a required slot to a form."""

    slot_name: str
    order: Optional[int] = None
    required: bool = True


class FormRequiredSlotUpdate(BaseModel):
    """Schema for updating a form required slot."""

    order: Optional[int] = None
    required: Optional[bool] = None


class FormRequiredSlotResponse(BaseModel):
    """Schema for form required slot response."""

    model_config = ConfigDict(from_attributes=True)

    id: str
    slot_name: str
    order: int
    required: bool
