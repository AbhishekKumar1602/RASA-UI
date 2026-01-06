from sqlalchemy.orm import Session
from app.utils.domain_yaml_writer import build_domain_yaml


def export_domain_yaml(
    db: Session,
    version_id: str,
) -> str:

    return build_domain_yaml(db, version_id)
