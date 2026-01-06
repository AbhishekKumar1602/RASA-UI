from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.project import ProjectCreate, ProjectResponse, ProjectLanguageCreate
from app.schemas.version import VersionResponse, VersionLanguageCreate, VersionLanguageResponse
from app.services.project_service import create_project, list_projects
from app.services.project_language_service import add_language_to_project, list_project_languages
from app.services.version_service import list_project_versions
from app.services.version_language_service import add_language_to_draft_version, list_version_languages
from app.services.promotion_service import promote_draft_to_production
from app.services.rollback_service import rollback_production


router = APIRouter(prefix="/projects", tags=["Projects"])


# -------------------------------------------------
# PROJECT CRUD
# -------------------------------------------------

@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=201,
)
def create_new_project(
    payload: ProjectCreate,
    db: Session = Depends(get_db),
):
    """Create a new project with initial draft and production versions."""
    return create_project(db, project_code=payload.project_code, project_name=payload.project_name)


@router.get(
    "/",
    response_model=List[ProjectResponse],
)
def get_projects(db: Session = Depends(get_db)):
    """List all projects."""
    return list_projects(db)


# -------------------------------------------------
# PROJECT LANGUAGES
# -------------------------------------------------

@router.post(
    "/{project_code}/languages",
    status_code=201,
)
def add_project_language(
    project_code: str,
    payload: ProjectLanguageCreate,
    db: Session = Depends(get_db),
):
    """Add a language to a project."""
    return add_language_to_project(db, project_code=project_code, language_code=payload.language_code)


@router.get(
    "/{project_code}/languages",
)
def get_project_languages(
    project_code: str,
    db: Session = Depends(get_db),
):
    """List all languages for a project."""
    rows = list_project_languages(db, project_code)
    return [
        {
            "language_code": lang.language_code,
            "language_name": lang.language_name,
        }
        for _, lang in rows
    ]


# -------------------------------------------------
# VERSIONS
# -------------------------------------------------

@router.get(
    "/{project_code}/versions",
    response_model=List[VersionResponse],
)
def get_project_versions(
    project_code: str,
    db: Session = Depends(get_db),
):
    """List all versions for a project."""
    versions = list_project_versions(db, project_code)
    return [
        VersionResponse(
            id=v.id,
            version_label=v.version_label,
            status=v.status,
            created_at=v.created_at,
        )
        for v in versions
    ]


# -------------------------------------------------
# VERSION LANGUAGES
# -------------------------------------------------

@router.post(
    "/{project_code}/versions/draft/languages",
    status_code=201,
)
def add_language_to_draft(
    project_code: str,
    payload: VersionLanguageCreate,
    db: Session = Depends(get_db),
):
    """Add a language to the draft version."""
    return add_language_to_draft_version(db, project_code=project_code, language_code=payload.language_code)


@router.get(
    "/{project_code}/versions/{status}/languages",
)
def get_version_languages(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    """List all languages for a version."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")

    rows = list_version_languages(db, project_code, status)
    return [
        {
            "language_code": lang.language_code,
            "language_name": lang.language_name,
        }
        for _, lang in rows
    ]


# -------------------------------------------------
# PROMOTION / ROLLBACK
# -------------------------------------------------

@router.post(
    "/{project_code}/promote",
)
def promote(
    project_code: str,
    db: Session = Depends(get_db),
):
    """Promote draft version to production."""
    return promote_draft_to_production(db, project_code)


@router.post(
    "/{project_code}/rollback",
)
def rollback(
    project_code: str,
    db: Session = Depends(get_db),
):
    """Rollback production to archived version."""
    return rollback_production(db, project_code)
