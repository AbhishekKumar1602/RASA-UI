import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    Boolean,
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


class Form(Base):

    __tablename__ = "forms"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    ignored_intents = Column(JSON, nullable=True)  # List of intent names to ignore during form
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    version = relationship("Version", back_populates="forms")
    required_slots = relationship("FormRequiredSlot", back_populates="form", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("version_id", "name", name="uq_form_name_per_version"),
        Index("ix_form_version", "version_id"),
    )


class FormRequiredSlot(Base):
    """
    Represents a required slot in a form with its order and required flag.
    """
    __tablename__ = "form_required_slots"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    form_id = Column(String, ForeignKey("forms.id"), nullable=False)
    slot_id = Column(String, ForeignKey("slots.id"), nullable=False)
    order = Column(Integer, nullable=False)
    required = Column(Boolean, default=True)
    
    form = relationship("Form", back_populates="required_slots")
    slot = relationship("Slot", back_populates="form_required_slots")
    mappings = relationship("FormSlotMapping", back_populates="form_required_slot", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("form_id", "slot_id", name="uq_form_required_slot"),
        Index("ix_form_required_slot_form", "form_id"),
    )


class FormSlotMapping(Base):

    __tablename__ = "form_slot_mappings"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    form_required_slot_id = Column(
        String, ForeignKey("form_required_slots.id"), nullable=False
    )
    mapping_type = Column(String, nullable=False)
    
    # For from_entity mapping
    entity_id = Column(String, ForeignKey("entities.id"), nullable=True)
    
    # For from_intent mapping
    intent = Column(String, nullable=True)
    not_intent = Column(String, nullable=True)
    value = Column(String, nullable=True)  # NEW - Value to set when intent matches
    
    # Relationships
    form_required_slot = relationship("FormRequiredSlot", back_populates="mappings")
    entity = relationship("Entity", back_populates="form_slot_mappings")

    __table_args__ = (
        CheckConstraint(
            "mapping_type IN ('from_entity','from_text','from_intent','from_trigger_intent')",
            name="ck_form_slot_mapping_type",
        ),
        Index("ix_form_slot_mapping_frs", "form_required_slot_id"),
    )
