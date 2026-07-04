from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.auth.dependencies import get_current_user, require_owner, require_admin_or_owner

from app.models.user import User

from app.connectors.schemas import (
    ConnectConnectorRequest,
    ConnectSuccessResponse,
    DisconnectConnectorRequest,
    DisconnectSuccessResponse,
    ConnectorResponse,
    ConnectorListResponse
)

from app.connectors.models import ConnectorProvider

from app.connectors.service import connector_service


router = APIRouter()


# =====================================================
# Connect (Owner only)
# =====================================================

@router.post(
    "/connect",
    response_model=ConnectSuccessResponse
)
async def connect_connector(
    request: ConnectConnectorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):

    connector = await connector_service.connect(
        db=db,
        current_user=current_user,
        provider=request.provider,
        token=request.token
    )

    return {
        "success": True,
        "message": f"{request.provider.value} connected successfully.",
        "connector": connector
    }


# =====================================================
# Get All Connectors (Admin/Owner only)
# =====================================================

@router.get(
    "",
    response_model=ConnectorListResponse
)
async def list_connectors(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):

    connectors = await connector_service.get_connectors(
        db=db,
        current_user=current_user
    )

    return {
        "connectors": connectors
    }


# =====================================================
# Get One Connector (Admin/Owner only)
# =====================================================

@router.get(
    "/{provider}",
    response_model=ConnectorResponse
)
async def get_connector(
    provider: ConnectorProvider,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner)
):

    connector = await connector_service.get_connector(
        db=db,
        current_user=current_user,
        provider=provider
    )

    return connector


# =====================================================
# Disconnect (Owner only)
# =====================================================

@router.delete(
    "/disconnect",
    response_model=DisconnectSuccessResponse
)
async def disconnect_connector(
    request: DisconnectConnectorRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner)
):

    return await connector_service.disconnect(
        db=db,
        current_user=current_user,
        provider=request.provider
    )