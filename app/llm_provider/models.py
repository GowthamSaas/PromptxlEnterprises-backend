from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base
from app.models.user import User


class LLMProvider(Base):
    __tablename__ = "llm_providers"
    __table_args__ = (
    UniqueConstraint(
        "tenant_id",
        "provider",
        name="uq_llm_tenant_provider",
    ),
)

    id = Column(Integer, primary_key=True, index=True)
    tenant_id = Column(
    Integer,
    ForeignKey("tenants.id", ondelete="CASCADE"),
    nullable=False,
    index=True,
    )

    connected_by = Column(
    Integer,
    ForeignKey("users.id"),
    nullable=False,)
    provider = Column(String(50), nullable=False)
    encrypted_api_key = Column(String(512), nullable=False)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    tenant = relationship(
    "Tenant",
    back_populates="llm_providers",
   )

    connected_user = relationship(
    "User",
    back_populates="connected_llm_providers",
    foreign_keys=[connected_by],
)