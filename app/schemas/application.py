from pydantic import BaseModel, HttpUrl
from typing import Optional
from datetime import datetime

class ApplicationBase(BaseModel):
    name: str
    description: Optional[str] = None
    icon_url: str
    launch_url: str

class ApplicationCreate(ApplicationBase):
    pass

class ApplicationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    icon_url: Optional[str] = None
    launch_url: Optional[str] = None
    is_active: Optional[bool] = None

class ApplicationResponse(ApplicationBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None
    created_by: int

    class Config:
        from_attributes = True
