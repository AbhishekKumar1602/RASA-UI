from pydantic import BaseModel
from typing import List, Dict, Any, Optional


class ExportRequest(BaseModel):
    project_id: str
    language: str
    version_label: str


class NLUBlock(BaseModel):
    intent: Optional[str] = None
    regex: Optional[str] = None
    lookup: Optional[str] = None
    synonym: Optional[str] = None
    examples: str


class NLUExportResponse(BaseModel):
    version: str
    nlu: List[NLUBlock]


class DomainExportResponse(BaseModel):
    version: str
    intents: List[str]
    entities: List[Any]
    slots: Dict[str, Any]
    forms: Dict[str, Any]
    responses: Dict[str, Any]
    actions: List[str]
    session_config: Optional[Dict[str, Any]] = None


class StoriesExportResponse(BaseModel):
    version: str
    stories: List[Dict[str, Any]]


class RulesExportResponse(BaseModel):
    version: str
    rules: List[Dict[str, Any]]
