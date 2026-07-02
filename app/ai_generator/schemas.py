from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class GenerateAppRequest(BaseModel):
    prompt: str = Field(..., min_length=3, description="User description of the app to generate")
    app_name: Optional[str] = Field(None, max_length=100)
    template: Optional[str] = Field(None, description="Optional template or starter style")
    provider: Optional[str] = Field("openai", description="Preferred provider")
    stream: bool = False


class GeneratedFile(BaseModel):
    path: str
    content: str


class GenerateAppResponse(BaseModel):
    success: bool
    app_name: Optional[str] = None
    provider: Optional[str] = None
    files: List[GeneratedFile] = []
    summary: Optional[str] = None
    message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class GenerationStatusResponse(BaseModel):
    status: str
    message: str
    job_id: Optional[str] = None
