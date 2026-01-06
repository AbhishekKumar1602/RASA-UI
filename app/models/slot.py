import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    Float,
    ForeignKey,
    DateTime,
    JSON,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Slot(Base):
    __tablename__ = "slots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)

    slot_type = Column(String, nullable=False)
    influence_conversation = Column(Boolean, default=True)

    initial_value = Column(String, nullable=True)
    values = Column(JSON, nullable=True)          # For categorical slots
    min_value = Column(Float, nullable=True)
    max_value = Column(Float, nullable=True)

    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    version = relationship("Version", back_populates="slots")
    mappings = relationship(
        "SlotMapping",
        back_populates="slot",
        cascade="all, delete-orphan",
    )
    form_required_slots = relationship(
        "FormRequiredSlot",
        back_populates="slot",
    )

    __table_args__ = (
        UniqueConstraint(
            "version_id",
            "name",
            name="uq_slot_name_per_version",
        ),
        CheckConstraint(
            "slot_type IN ('text','bool','float','list','categorical','any')",
            name="ck_slot_type",
        ),
        Index("ix_slot_version", "version_id"),
    )


class SlotMapping(Base):

    __tablename__ = "slot_mappings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    slot_id = Column(String, ForeignKey("slots.id"), nullable=False)

    mapping_type = Column(String, nullable=False)

    # from_entity mapping fields
    entity_id = Column(String, ForeignKey("entities.id"), nullable=True)
    role = Column(String, nullable=True)
    group = Column(String, nullable=True)

    # from_intent / from_trigger_intent mapping fields
    intent = Column(String, nullable=True)
    not_intent = Column(String, nullable=True)
    value = Column(String, nullable=True)

    # Conditions (replaces single active_loop)
    conditions = Column(JSON, nullable=True)

    # Legacy field (backward compatibility)
    active_loop = Column(String, nullable=True)

    priority = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())

    # Relationships
    slot = relationship("Slot", back_populates="mappings")
    entity = relationship("Entity", back_populates="slot_mappings")

    __table_args__ = (
        CheckConstraint(
            "mapping_type IN ('from_entity','from_text','from_intent','from_trigger_intent','custom')",
            name="ck_slot_mapping_type",
        ),
        Index("ix_slot_mapping_slot", "slot_id"),
    )

