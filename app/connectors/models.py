from sqlalchemy import (
    Column,
    Integer,
    String,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    JSON,
    UniqueConstraint
)

from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

import enum


class ConnectorProvider(str, enum.Enum):
    VERCEL = "vercel"
    GITHUB = "github"
    SUPABASE = "supabase"


class Connector(Base):
    __tablename__ = "connectors"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "provider",
            name="uq_tenant_provider"
        ),
    )

    # --------------------------------------------------
    # Primary Key
    # --------------------------------------------------

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # --------------------------------------------------
    # Tenant
    # --------------------------------------------------

    tenant_id = Column(
        Integer,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # --------------------------------------------------
    # Created By (Owner/Admin)
    # --------------------------------------------------

    created_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False
    )

    # --------------------------------------------------
    # Connector Provider
    # --------------------------------------------------

    provider = Column(
        Enum(
            ConnectorProvider,
            name="connector_provider"
        ),
        nullable=False
    )

    # --------------------------------------------------
    # Encrypted Access Token
    # --------------------------------------------------

    encrypted_token = Column(
        String(1000),
        nullable=False
    )

    # --------------------------------------------------
    # Account Name
    # --------------------------------------------------

    account_name = Column(
        String(255),
        nullable=True
    )

    # --------------------------------------------------
    # Provider Metadata
    #
    # Vercel:
    # {
    #     "teams": 1
    # }
    #
    # GitHub:
    # {
    #     "repositories": 25
    # }
    #
    # Supabase:
    # {
    #     "projects": 3,
    #     "tables": 42
    # }
    # --------------------------------------------------

    provider_metadata = Column(
        JSON,
        nullable=True
    )

    # --------------------------------------------------
    # Connection Status
    # --------------------------------------------------

    connected = Column(
        Boolean,
        default=True,
        nullable=False
    )

    connected_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )

    disconnected_at = Column(
        DateTime(timezone=True),
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
        back_populates="connectors"
    )

    creator = relationship(
    "User",
    back_populates="created_connectors",
    foreign_keys=[created_by]
    )