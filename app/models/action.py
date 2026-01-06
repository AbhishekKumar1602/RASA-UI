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


class Action(Base):

    __tablename__ = "actions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    version = relationship("Version", back_populates="actions")

    __table_args__ = (
        UniqueConstraint("version_id", "name", name="uq_action_name_per_version"),
        Index("ix_action_version", "version_id"),
    )
