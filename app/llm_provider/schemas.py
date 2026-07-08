from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

ProviderName = Literal["openai", "claude", "gemini" , "minimax"]


class ConnectProviderRequest(BaseModel):
    provider: ProviderName = Field(..., description="Provider name")
    api_key: str = Field(..., min_length=1, description="API key for the provider")


class DisconnectProviderRequest(BaseModel):
    provider: ProviderName = Field(..., description="Provider name")


class ProviderResponse(BaseModel):
    id: int
    tenant_id: int
    connected_by_id: int
    provider: str
    validated_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    # ---------- Admin UI ----------
    owner_connected: bool = False
    connected_by: Optional[str] = None
    connected_on: Optional[datetime] = None
    last_used: Optional[datetime] = None

    class Config:
        from_attributes = True


class ProviderListResponse(BaseModel):
    providers: List[ProviderResponse]
    count: int

    class Config:
        from_attributes = True
