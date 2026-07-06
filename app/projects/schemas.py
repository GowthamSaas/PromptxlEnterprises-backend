from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectCreateRequest(BaseModel):
    name: str = Field(
        ...,
        min_length=2,
        max_length=255,
    )
    description: Optional[str] = None
    provider: str
    model: str


class ProjectUpdateRequest(BaseModel):
    name: Optional[str] = Field(
        default=None,
        min_length=2,
        max_length=255,
    )
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    provider: str
    model: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProjectExportResponse(BaseModel):
    message: str
    download_url: Optional[str] = None