from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.dependencies import get_db
from app.schemas.session_config import SessionConfigCreate, SessionConfigResponse
from app.services.session_config_service import upsert_session_config


router = APIRouter(prefix="/projects", tags=["Session Config"])


@router.put(
    "/{project_code}/versions/draft/session-config",
    response_model=SessionConfigResponse,
)
def upsert_session_config_endpoint(
    project_code: str,
    payload: SessionConfigCreate,
    db: Session = Depends(get_db),
):
    """Create or update session config for the draft version."""
    return upsert_session_config(db, project_code, payload)
