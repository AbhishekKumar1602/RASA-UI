from pydantic import BaseModel, ConfigDict
from typing import List


class LookupCreate(BaseModel):
    lookup_name: str
    entity_key: str


class LookupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    lookup_name: str
    entity_key: str


class LookupExampleUpsert(BaseModel):
    language_code: str
    examples: List[str]


class LookupExampleResponse(BaseModel):
    lookup_name: str
    language_code: str
    example_count: int
