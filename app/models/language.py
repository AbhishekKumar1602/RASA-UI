import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Language(Base):
    __tablename__ = "languages"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    language_code = Column(String, unique=True, nullable=False)
    language_name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    project_languages = relationship("ProjectLanguage", back_populates="language")
    version_languages = relationship("VersionLanguage", back_populates="language")

    __table_args__ = (
        Index("ix_language_code", "language_code"),
    )
