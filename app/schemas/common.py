from pydantic import BaseModel
from typing import Optional


class VersionRef(BaseModel):
    project_id: str
    language: str
    version_label: str


class MessageResponse(BaseModel):
    message: str


class ErrorResponse(BaseModel):
    detail: str
