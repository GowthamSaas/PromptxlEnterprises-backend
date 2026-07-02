from sqlalchemy import Column, Integer, String, Boolean, Enum, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class UserRole(str, enum.Enum):
    OWNER = "owner"
    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    USER = "user"

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole, name="userrole"), default=UserRole.USER, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=True)  # ID of user who created this account
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    # Relationships
    tenant = relationship("Tenant", back_populates="users", foreign_keys=[tenant_id])
    assigned_applications = relationship(
        "UserApplication",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    llm_providers = relationship(
        "LLMProvider",
        back_populates="user",
        cascade="all, delete-orphan"
    )
