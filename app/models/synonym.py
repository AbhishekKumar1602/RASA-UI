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


class Synonym(Base):
    __tablename__ = "synonyms"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    canonical_value = Column(String, nullable=False)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    version = relationship("Version", back_populates="synonyms")
    entity = relationship("Entity", back_populates="synonyms")
    examples = relationship("SynonymExample", back_populates="synonym", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("version_id", "canonical_value", "entity_id", name="uq_synonym_per_version_entity"),
        Index("ix_synonym_version", "version_id"),
    )


class SynonymExample(Base):
    __tablename__ = "synonym_examples"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    synonym_id = Column(String, ForeignKey("synonyms.id"), nullable=False)
    language_id = Column(String, ForeignKey("languages.id"), nullable=False)
    example = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    synonym = relationship("Synonym", back_populates="examples")
    language = relationship("Language")

    __table_args__ = (
        UniqueConstraint("synonym_id", "language_id", "example", name="uq_synonym_example_per_language"),
        Index("ix_synonym_example_synonym", "synonym_id"),
    )
