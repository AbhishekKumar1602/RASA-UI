from pydantic import BaseModel, ConfigDict, Field
from typing import List, Optional, Literal


class EntityCreate(BaseModel):
    entity_key: str = Field(..., description="Entity identifier")
    entity_type: Literal["text", "numeric"]
    use_regex: bool = False
    use_lookup: bool = False
    influence_conversation: bool = False
    roles: Optional[List[str]] = []
    groups: Optional[List[str]] = []


class EntityUpdate(BaseModel):
    use_regex: Optional[bool] = None
    use_lookup: Optional[bool] = None
    influence_conversation: Optional[bool] = None
    roles: Optional[List[str]] = None
    groups: Optional[List[str]] = None


class EntityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    entity_key: str
    entity_type: str
    use_regex: bool
    use_lookup: bool
    influence_conversation: bool
    roles: List[str] = []
    groups: List[str] = []
