from sqlalchemy.orm import Session
from app.models.rule import Rule, RuleStep
from app.utils.rule_yaml_writer import build_rules_yaml


def export_rules_yaml(
    db: Session,
    version_id: str,
) -> str:
    rules = (
        db.query(Rule).filter(Rule.version_id == version_id).order_by(Rule.name).all()
    )

    steps = (
        db.query(RuleStep)
        .join(Rule)
        .filter(Rule.version_id == version_id)
        .order_by(RuleStep.step_order)
        .all()
    )

    return build_rules_yaml(rules, steps)
