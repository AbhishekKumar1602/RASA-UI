import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from app.db.base import Base


class Entity(Base):
    __tablename__ = "entities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    entity_key = Column(String, nullable=False)
    entity_type = Column(String, nullable=False)
    use_regex = Column(Boolean, default=False)
    use_lookup = Column(Boolean, default=False)
    influence_conversation = Column(Boolean, default=False)
    version = relationship("Version", back_populates="entities")
    roles = relationship("EntityRole", back_populates="entity", cascade="all, delete-orphan")
    groups = relationship("EntityGroup", back_populates="entity", cascade="all, delete-orphan")
    slot_mappings = relationship("SlotMapping", back_populates="entity")
    form_slot_mappings = relationship("FormSlotMapping", back_populates="entity")
    regexes = relationship("Regex", back_populates="entity")
    lookups = relationship("Lookup", back_populates="entity")
    synonyms = relationship("Synonym", back_populates="entity")

    __table_args__ = (
        UniqueConstraint("version_id", "entity_key", name="uq_entity_key_per_version"),
        Index("ix_entity_version", "version_id"),
    )


class EntityRole(Base):
    __tablename__ = "entity_roles"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    role = Column(String, nullable=False)
    entity = relationship("Entity", back_populates="roles")

    __table_args__ = (
        UniqueConstraint("entity_id", "role", name="uq_entity_role"),
    )


class EntityGroup(Base):
    __tablename__ = "entity_groups"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    group_name = Column(String, nullable=False)
    entity = relationship("Entity", back_populates="groups")

    __table_args__ = (
        UniqueConstraint("entity_id", "group_name", name="uq_entity_group"),
    )
