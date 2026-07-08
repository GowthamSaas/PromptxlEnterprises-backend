from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    prompt: str = Field(
        ...,
        min_length=1,
    )

    project_id: Optional[int] = None

    provider: Optional[str] = None
    session_id: Optional[int] = None

    model: Optional[str] = None


class ChatResponse(BaseModel):
    success: bool

    session_id: int

    message: str

    created_at: datetime


class ChatHistoryResponse(BaseModel):
    id: int

    role: str

    message: str

    created_at: datetime

    class Config:
        from_attributes = True


class ChatSessionResponse(BaseModel):
    id: int

    project_id: Optional[int]

    title: Optional[str]

    created_at: datetime

    class Config:
        from_attributes = True