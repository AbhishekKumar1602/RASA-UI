import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Project(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_code = Column(String, unique=True, nullable=False)
    project_name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    versions = relationship("Version", back_populates="project", cascade="all, delete-orphan")
    languages = relationship("ProjectLanguage", back_populates="project", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_project_code", "project_code"),
    )


class ProjectLanguage(Base):
    __tablename__ = "project_languages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    project_id = Column(String, ForeignKey("projects.id"), nullable=False)
    language_id = Column(String, ForeignKey("languages.id"), nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    project = relationship("Project", back_populates="languages")
    language = relationship("Language", back_populates="project_languages")

    __table_args__ = (
        UniqueConstraint("project_id", "language_id", name="uq_project_language"),
        Index("ix_project_language_project", "project_id"),
    )
