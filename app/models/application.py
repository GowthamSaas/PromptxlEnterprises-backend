from sqlalchemy import Column, Integer, String, Boolean, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

class Application(Base):
    __tablename__ = "applications"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=False)  # App icon is required per PRD
    launch_url = Column(String(500), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    created_by = Column(Integer, nullable=False)  # Owner or Admin who created it
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=True)
    
    # Relationships
    assigned_users = relationship(
        "UserApplication",
        back_populates="application",
        cascade="all, delete-orphan"
    )
