from pydantic import BaseModel, ConfigDict
from typing import List


class SynonymUpsert(BaseModel):
    entity_key: str
    canonical_value: str
    language_code: str
    examples: List[str]


class SynonymResponse(BaseModel):
    entity_key: str
    canonical_value: str
    language_code: str
    example_count: int


class SynonymListResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    entity_key: str
    canonical_value: str
