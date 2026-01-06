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


class Rule(Base):

    __tablename__ = "rules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    version = relationship("Version", back_populates="rules")
    conditions = relationship("RuleCondition", back_populates="rule", cascade="all, delete-orphan")
    steps = relationship("RuleStep", back_populates="rule", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("version_id", "name", name="uq_rule_name_per_version"),
        Index("ix_rule_version", "version_id"),
    )


class RuleStep(Base):

    __tablename__ = "rule_steps"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String, ForeignKey("rules.id"), nullable=False)
    step_order = Column(Integer, nullable=False)
    step_type = Column(String, nullable=False)
    
    # For intent steps
    intent_id = Column(String, ForeignKey("intents.id"), nullable=True)
    
    # For action steps - can reference action, response, or form
    action_id = Column(String, ForeignKey("actions.id"), nullable=True)  # Custom actions (action_*)
    response_id = Column(String, ForeignKey("responses.id"), nullable=True)  # Utterances (utter_*)
    form_id = Column(String, ForeignKey("forms.id"), nullable=True)  # Forms (form activation)
    
    # For active_loop steps
    active_loop_value = Column(String, nullable=True)  # Form name or null to deactivate
    
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    rule = relationship("Rule", back_populates="steps")
    intent = relationship("Intent")
    action = relationship("Action")
    response = relationship("Response")
    form = relationship("Form")
    slot_events = relationship("RuleSlotEvent", back_populates="step", cascade="all, delete-orphan")
    entities = relationship("RuleStepEntity", back_populates="step", cascade="all, delete-orphan")  # NEW

    __table_args__ = (
        CheckConstraint(
            "step_type IN ('intent','action','active_loop','slot')",
            name="ck_rule_step_type",
        ),
        Index("ix_rule_step_rule", "rule_id"),
    )


class RuleSlotEvent(Base):

    __tablename__ = "rule_slot_events"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_step_id = Column(String, ForeignKey("rule_steps.id"), nullable=False)
    slot_id = Column(String, ForeignKey("slots.id"), nullable=False)
    value = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    step = relationship("RuleStep", back_populates="slot_events")
    slot = relationship("Slot")

    __table_args__ = (
        Index("ix_rule_slot_event_step", "rule_step_id"),
    )


class RuleStepEntity(Base):

    __tablename__ = "rule_step_entities"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_step_id = Column(String, ForeignKey("rule_steps.id"), nullable=False)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    value = Column(String, nullable=True)  # The expected entity value
    role = Column(String, nullable=True)  # Optional role
    group = Column(String, nullable=True)  # Optional group
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    step = relationship("RuleStep", back_populates="entities")
    entity = relationship("Entity")

    __table_args__ = (
        Index("ix_rule_step_entity_step", "rule_step_id"),
    )


class RuleCondition(Base):

    __tablename__ = "rule_conditions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    rule_id = Column(String, ForeignKey("rules.id"), nullable=False)
    condition_type = Column(String, nullable=False)
    
    # For slot conditions
    slot_name = Column(String, nullable=True)
    slot_value = Column(String, nullable=True)
    
    # For active_loop conditions
    active_loop = Column(String, nullable=True)  # Form name or null
    
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    
    # Relationships
    rule = relationship("Rule", back_populates="conditions")

    __table_args__ = (
        CheckConstraint(
            "condition_type IN ('slot','active_loop')",
            name="ck_rule_condition_type",
        ),
        Index("ix_rule_condition_rule", "rule_id"),
    )
