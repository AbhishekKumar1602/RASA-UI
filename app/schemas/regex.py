from pydantic import BaseModel, ConfigDict
from typing import List


class RegexCreate(BaseModel):
    regex_name: str
    entity_key: str


class RegexResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    regex_name: str
    entity_key: str


class RegexExampleUpsert(BaseModel):
    language_code: str
    examples: List[str]


class RegexExampleResponse(BaseModel):
    regex_name: str
    language_code: str
    example_count: int
