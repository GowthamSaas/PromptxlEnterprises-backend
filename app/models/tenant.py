from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    # --------------------------------------------------
    # Primary Key
    # --------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------
    # Tenant Details
    # --------------------------------------------------

    tenant_id = Column(
        String(100),
        unique=True,
        nullable=False
    )

    company_name = Column(
        String(255),
        nullable=False
    )

    contact_email = Column(
        String(255),
        nullable=False
    )

    contact_phone = Column(
        String(50),
        nullable=True
    )

    address = Column(
        String(512),
        nullable=True
    )

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=True
    )

    # --------------------------------------------------
    # Audit
    # --------------------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now()
    )

    # --------------------------------------------------
    # Relationships
    # --------------------------------------------------

    users = relationship(
        "User",
        back_populates="tenant",
        cascade="all, delete-orphan",
        foreign_keys="User.tenant_id"
    )

    connectors = relationship(
        "Connector",
        back_populates="tenant",
        cascade="all, delete-orphan"
    )