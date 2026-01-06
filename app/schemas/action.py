from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ActionCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ActionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class ActionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    description: Optional[str] = None
    created_at: Optional[datetime] = None