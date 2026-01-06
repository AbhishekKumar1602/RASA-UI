from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models import Action, Version, Project
from app.schemas.action import ActionCreate, ActionUpdate


def get_version_by_status(db: Session, project_code: str, status: str) -> Version:
    """Get version by project code and status."""
    project = db.query(Project).filter(Project.project_code == project_code).first()
    if not project:
        raise HTTPException(404, "Project not found")

    version = (
        db.query(Version)
        .filter(Version.project_id == project.id, Version.status == status)
        .first()
    )
    if not version:
        raise HTTPException(404, f"Version with status '{status}' not found")

    return version


def create_action(db: Session, project_code: str, payload: ActionCreate) -> Action:
    """Create a new custom action in the draft version."""
    version = get_version_by_status(db, project_code, "draft")

    # Check for duplicate
    existing = (
        db.query(Action)
        .filter(Action.version_id == version.id, Action.name == payload.name)
        .first()
    )
    if existing:
        raise HTTPException(400, f"Action '{payload.name}' already exists")

    # Validate action name (should not start with utter_)
    if payload.name.startswith("utter_"):
        raise HTTPException(
            400,
            f"Action name '{payload.name}' starts with 'utter_'. "
            "Utterances should be created as Responses, not Actions.",
        )

    action = Action(
        version_id=version.id,
        name=payload.name,
        description=payload.description,
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


def list_actions(db: Session, project_code: str, status: str) -> list:
    """List all actions for a version."""
    version = get_version_by_status(db, project_code, status)

    return (
        db.query(Action)
        .filter(Action.version_id == version.id)
        .order_by(Action.name)
        .all()
    )


def get_action(db: Session, project_code: str, status: str, action_name: str) -> Action:
    """Get a specific action by name."""
    version = get_version_by_status(db, project_code, status)

    action = (
        db.query(Action)
        .filter(Action.version_id == version.id, Action.name == action_name)
        .first()
    )
    if not action:
        raise HTTPException(404, f"Action '{action_name}' not found")

    return action


def update_action(
    db: Session, project_code: str, action_name: str, payload: ActionUpdate
) -> Action:
    """Update an action in the draft version."""
    version = get_version_by_status(db, project_code, "draft")

    action = (
        db.query(Action)
        .filter(Action.version_id == version.id, Action.name == action_name)
        .first()
    )
    if not action:
        raise HTTPException(404, f"Action '{action_name}' not found")

    # Update name if provided
    if payload.name is not None:
        # Check for duplicate
        if payload.name != action_name:
            existing = (
                db.query(Action)
                .filter(Action.version_id == version.id, Action.name == payload.name)
                .first()
            )
            if existing:
                raise HTTPException(400, f"Action '{payload.name}' already exists")

            # Validate new name
            if payload.name.startswith("utter_"):
                raise HTTPException(
                    400,
                    f"Action name '{payload.name}' starts with 'utter_'. "
                    "Utterances should be created as Responses, not Actions.",
                )
        action.name = payload.name

    # Update description if provided
    if payload.description is not None:
        action.description = payload.description

    db.commit()
    db.refresh(action)
    return action


def delete_action(db: Session, project_code: str, action_name: str) -> None:
    """Delete an action from the draft version."""
    version = get_version_by_status(db, project_code, "draft")

    action = (
        db.query(Action)
        .filter(Action.version_id == version.id, Action.name == action_name)
        .first()
    )
    if not action:
        raise HTTPException(404, f"Action '{action_name}' not found")

    db.delete(action)
    db.commit()
