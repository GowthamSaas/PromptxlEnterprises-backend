from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    provider: Optional[str] = None
    model: Optional[str] = None
    application_id: Optional[int] = None
    stream: bool = False


class GenerateResponse(BaseModel):
    success: bool
    project_id: int
    project_name: str
    provider: str
    model: str
    response: Dict[str, Any]


class GenerateErrorResponse(BaseModel):
    success: bool = False
    message: str


class AIResponse(BaseModel):
    text: str
    raw_response: Optional[Dict[str, Any]] = None