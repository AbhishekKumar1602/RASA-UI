import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Story(Base):

    __tablename__ = "stories"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    version = relationship("Version", back_populates="stories")
    steps = relationship("StoryStep", back_populates="story", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("version_id", "name", name="uq_story_name_per_version"),
        Index("ix_story_version", "version_id"),
    )


class StoryStep(Base):

    __tablename__ = "story_steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    story_id = Column(String, ForeignKey("stories.id"), nullable=False)
    timeline_index = Column(Integer, nullable=False)  # For branching stories
    step_order = Column(Integer, nullable=False)
    step_type = Column(String, nullable=False)
    
    # For intent steps
    intent_id = Column(String, ForeignKey("intents.id"), nullable=True)
    
    # For action steps - can reference action, response, or form
    action_id = Column(String, ForeignKey("actions.id"), nullable=True)  # Custom actions (action_*)
    response_id = Column(String, ForeignKey("responses.id"), nullable=True)  # Utterances (utter_*)
    form_id = Column(String, ForeignKey("forms.id"), nullable=True)  # Forms
    
    # For active_loop steps
    active_loop_value = Column(String, nullable=True)  # Form name or null
    
    # For checkpoint steps
    checkpoint_name = Column(String, nullable=True)
    
    # For OR condition grouping (NEW)
    # Steps with same or_group_id are grouped as OR alternatives
    or_group_id = Column(String, nullable=True)
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    story = relationship("Story", back_populates="steps")
    intent = relationship("Intent")
    action = relationship("Action")
    response = relationship("Response")
    form = relationship("Form")
    slot_events = relationship("StorySlotEvent", back_populates="step", cascade="all, delete-orphan")
    entities = relationship("StoryStepEntity", back_populates="step", cascade="all, delete-orphan")  # NEW

    __table_args__ = (
        CheckConstraint(
            "step_type IN ('intent','action','slot','active_loop','checkpoint','or')",
            name="ck_story_step_type",
        ),
        Index("ix_step_story", "story_id"),
        Index("ix_step_or_group", "or_group_id"),  # NEW
    )


class StorySlotEvent(Base):

    __tablename__ = "story_slot_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    story_step_id = Column(String, ForeignKey("story_steps.id"), nullable=False)
    slot_id = Column(String, ForeignKey("slots.id"), nullable=False)
    value = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    step = relationship("StoryStep", back_populates="slot_events")
    slot = relationship("Slot")

    __table_args__ = (
        Index("ix_story_slot_event_step", "story_step_id"),
    )


class StoryStepEntity(Base):

    __tablename__ = "story_step_entities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    story_step_id = Column(String, ForeignKey("story_steps.id"), nullable=False)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    value = Column(String, nullable=True)  # The expected entity value
    role = Column(String, nullable=True)  # Optional role
    group = Column(String, nullable=True)  # Optional group
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    step = relationship("StoryStep", back_populates="entities")
    entity = relationship("Entity")

    __table_args__ = (
        Index("ix_story_step_entity_step", "story_step_id"),
    )
