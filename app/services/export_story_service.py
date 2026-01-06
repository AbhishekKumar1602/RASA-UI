from sqlalchemy.orm import Session
from app.models.story import Story, StoryStep
from app.utils.story_yaml_writer import build_stories_yaml


def export_stories_yaml(
    db: Session,
    version_id: str,
) -> str:
    stories = (
        db.query(Story)
        .filter(Story.version_id == version_id)
        .order_by(Story.name)
        .all()
    )

    steps = (
        db.query(StoryStep)
        .join(Story)
        .filter(Story.version_id == version_id)
        .order_by(StoryStep.step_order)
        .all()
    )

    return build_stories_yaml(stories, steps)
