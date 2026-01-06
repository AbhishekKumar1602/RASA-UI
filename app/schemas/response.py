from pydantic import BaseModel, ConfigDict
from typing import Optional, List, Any, Dict
from datetime import datetime


class ResponseComponentCreate(BaseModel):
    component_type: str
    payload: Any = None


class ResponseComponentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    component_type: str
    payload: Any = None
    order_index: int = 0


class ResponseConditionCreate(BaseModel):
    condition_type: str
    slot_name: Optional[str] = None
    slot_value: Optional[str] = None


class ResponseConditionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    condition_type: str
    slot_name: Optional[str] = None
    slot_value: Optional[str] = None
    order_index: int = 0


class ResponseVariantCreate(BaseModel):
    language_code: Optional[str] = None
    priority: Optional[int] = 0
    components: List[ResponseComponentCreate] = []
    conditions: List[ResponseConditionCreate] = []


class ResponseVariantUpdate(BaseModel):
    language_code: Optional[str] = None
    priority: Optional[int] = None


class ResponseVariantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    language_code: Optional[str] = None
    priority: int = 0
    components: List[ResponseComponentResponse] = []
    conditions: List[ResponseConditionResponse] = []


class ResponseCreate(BaseModel):
    name: str


class ResponseUpdate(BaseModel):
    name: Optional[str] = None


class ResponseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    created_at: Optional[datetime] = None


class ResponseDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    variants: List[ResponseVariantResponse] = []
    created_at: Optional[datetime] = None


class ResponseUpsertVariant(BaseModel):
    language_code: Optional[str] = None
    priority: Optional[int] = 0
    text: Optional[str] = None
    buttons: Optional[List[Dict[str, str]]] = None
    image: Optional[str] = None
    custom: Optional[Dict[str, Any]] = None
    attachment: Optional[Dict[str, Any]] = None
    conditions: Optional[List[ResponseConditionCreate]] = None


class ResponseUpsert(BaseModel):
    name: str
    variants: List[ResponseUpsertVariant] = []
