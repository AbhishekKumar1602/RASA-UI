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


class Regex(Base):
    __tablename__ = "regexes"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    regex_name = Column(String, nullable=False)
    entity_id = Column(String, ForeignKey("entities.id"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    version = relationship("Version", back_populates="regexes")
    entity = relationship("Entity", back_populates="regexes")
    examples = relationship("RegexExample", back_populates="regex", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("version_id", "regex_name", name="uq_regex_name_per_version"),
        Index("ix_regex_version", "version_id"),
    )


class RegexExample(Base):
    __tablename__ = "regex_examples"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    regex_id = Column(String, ForeignKey("regexes.id"), nullable=False)
    language_id = Column(String, ForeignKey("languages.id"), nullable=False)
    example = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    regex = relationship("Regex", back_populates="examples")
    language = relationship("Language")

    __table_args__ = (
        UniqueConstraint("regex_id", "language_id", "example", name="uq_regex_example_per_language"),
        Index("ix_regex_example_regex", "regex_id"),
    )
