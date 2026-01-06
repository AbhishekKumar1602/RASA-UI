from pydantic import BaseModel, ConfigDict
from datetime import datetime


class VersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    version_label: str
    status: str
    created_at: datetime


class VersionLanguageCreate(BaseModel):
    language_code: str


class VersionLanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    language_code: str
    language_name: str
    is_default: bool
