import uuid
from sqlalchemy import (
    Column,
    String,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Intent(Base):
    __tablename__ = "intents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    intent_name = Column(String, nullable=False)
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    version = relationship("Version", back_populates="intents")
    localizations = relationship(
        "IntentLocalization",
        back_populates="intent",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("version_id", "intent_name", name="uq_intent_name_per_version"),
        Index("ix_intent_version", "version_id"),
    )


class IntentLocalization(Base):
    __tablename__ = "intent_localizations"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    intent_id = Column(String, ForeignKey("intents.id"), nullable=False)
    language_id = Column(String, ForeignKey("languages.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    intent = relationship("Intent", back_populates="localizations")
    language = relationship("Language")
    examples = relationship(
        "IntentExample",
        back_populates="localization",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("intent_id", "language_id", name="uq_intent_language"),
        Index("ix_localization_intent", "intent_id"),
    )


class IntentExample(Base):
    __tablename__ = "intent_examples"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    intent_localization_id = Column(
        String, ForeignKey("intent_localizations.id"), nullable=False
    )
    example = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    localization = relationship("IntentLocalization", back_populates="examples")

    __table_args__ = (
        Index("ix_example_localization", "intent_localization_id"),
    )
