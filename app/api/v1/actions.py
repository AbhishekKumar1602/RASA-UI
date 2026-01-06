from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.dependencies import get_db
from app.schemas.action import ActionCreate, ActionUpdate, ActionResponse
from app.services.action_service import (
    create_action,
    list_actions,
    get_action,
    update_action,
    delete_action,
)


router = APIRouter(prefix="/projects", tags=["Actions"])


@router.post(
    "/{project_code}/versions/draft/actions",
    response_model=ActionResponse,
    status_code=201,
)
def create_action_endpoint(
    project_code: str,
    payload: ActionCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new custom action in the draft version.

    Custom actions are Python functions that perform operations like:
    - Fetching data from external APIs
    - Saving data to databases
    - Form validation

    The action name should NOT start with 'utter_' - those are responses.

    Examples:
    - action_fetch_bill
    - action_clear_slots
    - action_save_request
    - validate_request_form
    """
    return create_action(db, project_code, payload)


@router.get(
    "/{project_code}/versions/{status}/actions",
    response_model=List[ActionResponse],
)
def list_actions_endpoint(
    project_code: str,
    status: str,
    db: Session = Depends(get_db),
):
    """List all custom actions for a version."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return list_actions(db, project_code, status)


@router.get(
    "/{project_code}/versions/{status}/actions/{action_name}",
    response_model=ActionResponse,
)
def get_action_endpoint(
    project_code: str,
    status: str,
    action_name: str,
    db: Session = Depends(get_db),
):
    """Get a specific custom action."""
    if status not in ("draft", "locked", "archived"):
        raise HTTPException(400, "Invalid version status")
    return get_action(db, project_code, status, action_name)


@router.put(
    "/{project_code}/versions/draft/actions/{action_name}",
    response_model=ActionResponse,
)
def update_action_endpoint(
    project_code: str,
    action_name: str,
    payload: ActionUpdate,
    db: Session = Depends(get_db),
):
    """Update a custom action in the draft version."""
    return update_action(db, project_code, action_name, payload)


@router.delete(
    "/{project_code}/versions/draft/actions/{action_name}",
    status_code=204,
)
def delete_action_endpoint(
    project_code: str,
    action_name: str,
    db: Session = Depends(get_db),
):
    """Delete a custom action from the draft version."""
    delete_action(db, project_code, action_name)
    return None
