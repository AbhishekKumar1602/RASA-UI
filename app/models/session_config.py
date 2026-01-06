import uuid
from sqlalchemy import (
    Column,
    String,
    Boolean,
    Integer,
    ForeignKey,
    DateTime,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class SessionConfig(Base):
    __tablename__ = "session_configs"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    session_expiration_time = Column(Integer, nullable=False, default=60)
    carry_over_slots_to_new_session = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    version = relationship("Version", back_populates="session_config")

    __table_args__ = (
        UniqueConstraint("version_id", name="uq_session_config_per_version"),
        Index("ix_session_config_version", "version_id"),
    )
