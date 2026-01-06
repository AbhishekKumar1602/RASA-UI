from pydantic import BaseModel, ConfigDict
from datetime import datetime


class LanguageCreate(BaseModel):
    language_code: str
    language_name: str


class LanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    language_code: str
    language_name: str
    created_at: datetime
