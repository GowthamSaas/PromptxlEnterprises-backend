from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base


class AIAgentConnection(Base):
    __tablename__ = "ai_agent_connections"

    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "connected_by",
            name="uq_ai_agent_tenant_user",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    # PromptXL tenant
    tenant_id = Column(
        Integer,
        ForeignKey(
            "tenants.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # PromptXL user
    connected_by = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    # External API token
    encrypted_api_token = Column(
        String(1024),
        nullable=False,
    )

    # External API tenant
    external_tenant = Column(
        String(255),
        nullable=False,
    )

    tenant = relationship(
        "Tenant",
        back_populates="ai_agent_connections",
    )

    connected_user = relationship(
        "User",
        back_populates="ai_agent_connections",
        foreign_keys=[connected_by],
    )

    endpoints = relationship(
        "AIAgentEndpoint",
        back_populates="connection",
        cascade="all, delete-orphan",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class AIAgentEndpoint(Base):
    __tablename__ = "ai_agent_endpoints"

    __table_args__ = (
        UniqueConstraint(
            "connection_id",
            "endpoint",
            name="uq_ai_agent_connection_endpoint",
        ),
    )

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    connection_id = Column(
        Integer,
        ForeignKey(
            "ai_agent_connections.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    # External API endpoint
    endpoint = Column(
        String(2048),
        nullable=False,
    )

    # HTTP method (GET, POST, PUT, PATCH, DELETE)
    method = Column(
        String(10),
        nullable=True,
    )

    # Human-readable description of what this endpoint does
    description = Column(
        String(1024),
        nullable=True,
    )

    # Resource name extracted from endpoint (e.g., "customers", "orders", "lists")
    resource_name = Column(
        String(255),
        nullable=True,
    )

    # OpenAPI request schema (JSON)
    request_schema = Column(
        String(4096),
        nullable=True,
    )

    # OpenAPI response schema (JSON)
    response_schema = Column(
        String(4096),
        nullable=True,
    )

    connection = relationship(
        "AIAgentConnection",
        back_populates="endpoints",
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )