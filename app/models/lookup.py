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


class Lookup(Base):
    __tablename__ = "lookups"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    lookup_name = Column(String, nullable=False)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    version = relationship("Version", back_populates="lookups")
    entity = relationship("Entity", back_populates="lookups")
    examples = relationship("LookupExample", back_populates="lookup", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("version_id", "lookup_name", name="uq_lookup_name_per_version"),
        Index("ix_lookup_version", "version_id"),
    )


class LookupExample(Base):
    __tablename__ = "lookup_examples"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    lookup_id = Column(String, ForeignKey("lookups.id"), nullable=False)
    language_id = Column(String, ForeignKey("languages.id"), nullable=False)
    example = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    lookup = relationship("Lookup", back_populates="examples")
    language = relationship("Language")

    __table_args__ = (
        UniqueConstraint("lookup_id", "language_id", "example", name="uq_lookup_example_per_language"),
        Index("ix_lookup_example_lookup", "lookup_id"),
    )
