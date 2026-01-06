import uuid
from sqlalchemy import (
    Column,
    String,
    Integer,
    ForeignKey,
    DateTime,
    JSON,
    UniqueConstraint,
    CheckConstraint,
    Index,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base


class Response(Base):

    __tablename__ = "responses"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    version_id = Column(String, ForeignKey("versions.id"), nullable=False)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    version = relationship("Version", back_populates="responses")
    variants = relationship(
        "ResponseVariant", back_populates="response", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("version_id", "name", name="uq_response_name_per_version"),
        Index("ix_response_version", "version_id"),
    )


class ResponseVariant(Base):

    __tablename__ = "response_variants"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    response_id = Column(String, ForeignKey("responses.id"), nullable=False)
    language_id = Column(String, ForeignKey("languages.id"), nullable=True)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    response = relationship("Response", back_populates="variants")
    language = relationship("Language")
    conditions = relationship(
        "ResponseCondition", back_populates="variant", cascade="all, delete-orphan"
    )
    components = relationship(
        "ResponseComponent", back_populates="variant", cascade="all, delete-orphan"
    )

    __table_args__ = (Index("ix_response_variant_response", "response_id"),)


class ResponseCondition(Base):

    __tablename__ = "response_conditions"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    response_variant_id = Column(
        String, ForeignKey("response_variants.id"), nullable=False
    )
    condition_type = Column(String, nullable=False)
    slot_name = Column(String, nullable=True)
    slot_value = Column(String, nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    variant = relationship("ResponseVariant", back_populates="conditions")

    __table_args__ = (
        CheckConstraint(
            "condition_type IN ('slot', 'active_loop')",
            name="ck_response_condition_type",
        ),
        Index("ix_response_condition_variant", "response_variant_id"),
    )


class ResponseComponent(Base):

    __tablename__ = "response_components"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    response_variant_id = Column(
        String, ForeignKey("response_variants.id"), nullable=False
    )
    component_type = Column(String, nullable=False)
    payload = Column(JSON, nullable=True)
    order_index = Column(Integer, default=0)
    created_at = Column(DateTime, server_default=func.now())
    variant = relationship("ResponseVariant", back_populates="components")

    __table_args__ = (
        CheckConstraint(
            "component_type IN ('text', 'buttons', 'image', 'custom', 'attachment')",
            name="ck_response_component_type",
        ),
        Index("ix_response_component_variant", "response_variant_id"),
    )
