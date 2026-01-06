from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.entity import Entity, EntityRole, EntityGroup
from app.services.common import get_version_by_status, get_draft_version


def create_entity(db: Session, project_code: str, payload):
    version = get_draft_version(db, project_code)

    if payload.entity_type not in ("text", "numeric"):
        raise HTTPException(400, "entity_type must be 'text' or 'numeric'")

    if payload.entity_type == "numeric" and payload.use_lookup:
        raise HTTPException(400, "Lookup is not allowed for numeric entities")

    existing = (
        db.query(Entity)
        .filter(
            Entity.version_id == version.id,
            Entity.entity_key == payload.entity_key,
        )
        .first()
    )
    if existing:
        raise HTTPException(400, "Entity already exists in draft version")

    entity = Entity(
        entity_key=payload.entity_key,
        entity_type=payload.entity_type,
        version_id=version.id,
        use_regex=payload.use_regex,
        use_lookup=payload.use_lookup,
        influence_conversation=payload.influence_conversation,
    )
    db.add(entity)
    db.flush()

    roles = []
    for role in payload.roles or []:
        db.add(EntityRole(entity_id=entity.id, role=role))
        roles.append(role)

    groups = []
    for group in payload.groups or []:
        db.add(EntityGroup(entity_id=entity.id, group_name=group))
        groups.append(group)

    db.commit()
    db.refresh(entity)

    return entity, roles, groups


def list_entities(db: Session, project_code: str, status: str):
    version = get_version_by_status(db, project_code, status)

    entities = (
        db.query(Entity)
        .filter(Entity.version_id == version.id)
        .order_by(Entity.entity_key)
        .all()
    )

    response = []
    for e in entities:
        roles = [
            r.role
            for r in db.query(EntityRole).filter(EntityRole.entity_id == e.id).all()
        ]
        groups = [
            g.group_name
            for g in db.query(EntityGroup).filter(EntityGroup.entity_id == e.id).all()
        ]

        response.append(
            {
                "id": e.id,
                "entity_key": e.entity_key,
                "entity_type": e.entity_type,
                "use_regex": e.use_regex,
                "use_lookup": e.use_lookup,
                "influence_conversation": e.influence_conversation,
                "roles": roles,
                "groups": groups,
            }
        )

    return response


def get_entity(db: Session, project_code: str, status: str, entity_key: str):
    version = get_version_by_status(db, project_code, status)

    entity = (
        db.query(Entity)
        .filter(
            Entity.version_id == version.id,
            Entity.entity_key == entity_key,
        )
        .first()
    )
    if not entity:
        raise HTTPException(404, "Entity not found")

    roles = [
        r.role
        for r in db.query(EntityRole).filter(EntityRole.entity_id == entity.id).all()
    ]
    groups = [
        g.group_name
        for g in db.query(EntityGroup).filter(EntityGroup.entity_id == entity.id).all()
    ]

    return {
        "id": entity.id,
        "entity_key": entity.entity_key,
        "entity_type": entity.entity_type,
        "use_regex": entity.use_regex,
        "use_lookup": entity.use_lookup,
        "influence_conversation": entity.influence_conversation,
        "roles": roles,
        "groups": groups,
    }


def update_entity(db: Session, project_code: str, entity_key: str, payload):
    version = get_draft_version(db, project_code)

    entity = (
        db.query(Entity)
        .filter(
            Entity.version_id == version.id,
            Entity.entity_key == entity_key,
        )
        .first()
    )
    if not entity:
        raise HTTPException(404, "Entity not found")

    if payload.use_lookup is True and entity.entity_type == "numeric":
        raise HTTPException(400, "Lookup is not allowed for numeric entities")

    if payload.use_regex is not None:
        entity.use_regex = payload.use_regex
    if payload.use_lookup is not None:
        entity.use_lookup = payload.use_lookup
    if payload.influence_conversation is not None:
        entity.influence_conversation = payload.influence_conversation

    if payload.roles is not None:
        db.query(EntityRole).filter(EntityRole.entity_id == entity.id).delete()
        for role in payload.roles:
            db.add(EntityRole(entity_id=entity.id, role=role))

    if payload.groups is not None:
        db.query(EntityGroup).filter(EntityGroup.entity_id == entity.id).delete()
        for group in payload.groups:
            db.add(EntityGroup(entity_id=entity.id, group_name=group))

    db.commit()
    db.refresh(entity)

    roles = [
        r.role
        for r in db.query(EntityRole).filter(EntityRole.entity_id == entity.id).all()
    ]
    groups = [
        g.group_name
        for g in db.query(EntityGroup).filter(EntityGroup.entity_id == entity.id).all()
    ]

    return {
        "id": entity.id,
        "entity_key": entity.entity_key,
        "entity_type": entity.entity_type,
        "use_regex": entity.use_regex,
        "use_lookup": entity.use_lookup,
        "influence_conversation": entity.influence_conversation,
        "roles": roles,
        "groups": groups,
    }


def delete_entity(db: Session, project_code: str, entity_key: str):
    version = get_draft_version(db, project_code)

    entity = (
        db.query(Entity)
        .filter(
            Entity.version_id == version.id,
            Entity.entity_key == entity_key,
        )
        .first()
    )
    if not entity:
        raise HTTPException(404, "Entity not found")

    db.query(EntityRole).filter(EntityRole.entity_id == entity.id).delete()
    db.query(EntityGroup).filter(EntityGroup.entity_id == entity.id).delete()

    db.delete(entity)
    db.commit()
