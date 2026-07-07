from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    Enum,
    DateTime,
    ForeignKey
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.project_assignments.models import ProjectAssignment

import enum


class UserRole(str, enum.Enum):
    OWNER = "owner"
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"


class User(Base):
    __tablename__ = "users"

    # --------------------------------------------------
    # Primary Key
    # --------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------
    # User Information
    # --------------------------------------------------

    email = Column(
        String(255),
        unique=True,
        index=True,
        nullable=False
    )

    hashed_password = Column(
        String(255),
        nullable=False
    )

    full_name = Column(
        String(255),
        nullable=False
    )

    role = Column(
        Enum(UserRole, name="userrole"),
        default=UserRole.USER,
        nullable=False
    )

    is_active = Column(
        Boolean,
        default=True
    )

    created_by = Column(
        Integer,
        nullable=True
    )

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id"),
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

    tenant = relationship(
        "Tenant",
        back_populates="users",
        foreign_keys=[tenant_id]
    )

    assigned_applications = relationship(
        "UserApplication",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    assigned_projects = relationship(
        "ProjectAssignment",
        back_populates="user",
        foreign_keys="ProjectAssignment.user_id",
        cascade="all, delete-orphan",
    )

    llm_providers = relationship(
        "LLMProvider",
        back_populates="user",
        cascade="all, delete-orphan"
    )

    # Connectors created by this Owner/Admin
    created_connectors = relationship(
        "Connector",
        back_populates="creator",
        foreign_keys="Connector.created_by",
        cascade="all, delete-orphan"
    )