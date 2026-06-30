from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class TenantBase(BaseModel):
    tenant_id: str
    company_name: str
    contact_email: EmailStr
    contact_phone: Optional[str] = None
    address: Optional[str] = None

class TenantCreate(TenantBase):
    owner_email: EmailStr
    owner_full_name: str
    owner_password: str
    pass

class TenantResponse(TenantBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
