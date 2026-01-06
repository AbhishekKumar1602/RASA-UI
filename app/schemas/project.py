from pydantic import BaseModel, ConfigDict
from datetime import datetime


class ProjectCreate(BaseModel):
    project_code: str
    project_name: str


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_code: str
    project_name: str
    created_at: datetime


class ProjectLanguageCreate(BaseModel):
    language_code: str


class ProjectLanguageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    language_code: str
    language_name: str
    is_default: bool
