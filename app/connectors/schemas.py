from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field

from app.connectors.models import ConnectorProvider


# =====================================================
# Connect Request
# =====================================================

class ConnectConnectorRequest(BaseModel):

    provider: ConnectorProvider

    token: str = Field(..., min_length=10)

    class Config:
        from_attributes = True


# =====================================================
# Disconnect Request
# =====================================================

class DisconnectConnectorRequest(BaseModel):

    provider: ConnectorProvider

    class Config:
        from_attributes = True


# =====================================================
# Connector Response
# =====================================================

class ConnectorResponse(BaseModel):

    id: int

    provider: ConnectorProvider

    connected: bool

    account_name: Optional[str] = None

    provider_metadata: Optional[Dict[str, Any]] = None

    connected_at: Optional[datetime] = None

    disconnected_at: Optional[datetime] = None

    created_at: Optional[datetime] = None

    updated_at: Optional[datetime] = None

    connected_by: Optional[str] = None
    last_used: Optional[datetime] = None


    class Config:
        from_attributes = True


# =====================================================
# Connector List Response
# =====================================================

class ConnectorListResponse(BaseModel):

    connectors: list[ConnectorResponse]

    class Config:
        from_attributes = True


# =====================================================
# Connect Success Response
# =====================================================

class ConnectSuccessResponse(BaseModel):

    success: bool

    message: str

    connector: ConnectorResponse

    class Config:
        from_attributes = True


# =====================================================
# Disconnect Success Response
# =====================================================

class DisconnectSuccessResponse(BaseModel):

    success: bool

    message: str

    class Config:
        from_attributes = True