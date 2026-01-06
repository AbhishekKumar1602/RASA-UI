from pydantic import BaseModel, ConfigDict
from typing import List, Optional


class IntentCreate(BaseModel):
    intent_name: str


class IntentUpdate(BaseModel):
    intent_name: Optional[str] = None


class IntentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    intent_name: str


class IntentExampleUpsert(BaseModel):
    language_code: str
    examples: List[str]


class IntentExampleResponse(BaseModel):
    intent_name: str
    language_code: str
    example_count: int
