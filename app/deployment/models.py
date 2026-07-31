from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    JSON,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class Deployment(Base):
    __tablename__ = "deployments"

    # ----------------------------------------
    # Primary Key
    # ----------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # ----------------------------------------
    # Tenant
    # ----------------------------------------

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ----------------------------------------
    # Project
    # ----------------------------------------

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # ----------------------------------------
    # User
    # ----------------------------------------

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    # ----------------------------------------
    # Deployment Provider
    # ----------------------------------------

    provider = Column(
        String(50),
        nullable=False,
    )

    # github / direct
    deployment_method = Column(
        String(50),
        nullable=False,
    )

    # ----------------------------------------
    # GitHub
    # ----------------------------------------

    repository_name = Column(
        String(255),
        nullable=True,
    )

    repository_url = Column(
        String(500),
        nullable=True,
    )

    # ----------------------------------------
    # Deployment
    # ----------------------------------------

    deployment_id = Column(
        String(255),
        nullable=True,
    )

    deployment_url = Column(
        String(500),
        nullable=True,
    )

    # queued
    # deploying
    # ready
    # failed

    status = Column(
        String(50),
        default="queued",
        nullable=False,
    )

    # ----------------------------------------
    # Metadata
    # ----------------------------------------

    deployment_metadata = Column(
        JSON,
        nullable=True,
    )

    logs = Column(
        Text,
        nullable=True,
    )

    # ----------------------------------------
    # Audit
    # ----------------------------------------

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    updated_at = Column(
        DateTime(timezone=True),
        onupdate=func.now(),
    )

    # ----------------------------------------
    # Relationships
    # ----------------------------------------

    tenant = relationship(
        "Tenant",
        back_populates="deployments",
    )

    project = relationship(
        "Project",
        back_populates="deployments",
    )

    creator = relationship(
        "User",
        back_populates="deployments",
        foreign_keys=[created_by],
    )