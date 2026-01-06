import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Version(Base):
    __tablename__ = "versions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    parent_version_id = Column(String, ForeignKey("versions.id"), nullable=True)
    version_label = Column(String, nullable=False)
    status = Column(String, nullable=False)
    created_by = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    project = relationship("Project", back_populates="versions")
    parent_version = relationship("Version", remote_side=[id], backref="child_versions")
    intents = relationship("Intent", back_populates="version", cascade="all, delete-orphan")
    entities = relationship("Entity", back_populates="version", cascade="all, delete-orphan")
    slots = relationship("Slot", back_populates="version", cascade="all, delete-orphan")
    stories = relationship("Story", back_populates="version", cascade="all, delete-orphan")
    rules = relationship("Rule", back_populates="version", cascade="all, delete-orphan")
    forms = relationship("Form", back_populates="version", cascade="all, delete-orphan")
    actions = relationship("Action", back_populates="version", cascade="all, delete-orphan")  
    responses = relationship("Response", back_populates="version", cascade="all, delete-orphan") 
    regexes = relationship("Regex", back_populates="version", cascade="all, delete-orphan")
    lookups = relationship("Lookup", back_populates="version", cascade="all, delete-orphan")
    synonyms = relationship("Synonym", back_populates="version", cascade="all, delete-orphan")
    languages = relationship("VersionLanguage", back_populates="version", cascade="all, delete-orphan")
    session_config = relationship("SessionConfig", back_populates="version", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("project_id", "status", name="uq_project_single_version_per_status"),
        CheckConstraint("status IN ('draft','locked','archived')", name="ck_version_status"),
        Index("ix_version_project", "project_id"),
    )


class VersionLanguage(Base):
    __tablename__ = "version_languages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    language_id = Column(String, ForeignKey("languages.id"), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    version = relationship("Version", back_populates="languages")
    language = relationship("Language", back_populates="version_languages")

    __table_args__ = (
        UniqueConstraint("version_id", "language_id", name="uq_version_language"),
        Index("ix_version_language_version", "version_id"),
    )
