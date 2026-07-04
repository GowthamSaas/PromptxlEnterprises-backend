from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.user import User, UserRole

from app.connectors.models import ConnectorProvider
from app.connectors import crud

from app.connectors.services.connector_factory import (
    ConnectorFactory
)

from app.connectors.services.encryption_service import (
    encryption_service
)


class ConnectorService:

    # ----------------------------------------
    # Role Validation
    # ----------------------------------------

    def _check_permission(
        self,
        user: User
    ):

        if user.role not in [
            UserRole.OWNER,
            UserRole.ADMIN
        ]:

            raise HTTPException(
                status_code=403,
                detail="Only Owner and Admin can manage connectors."
            )

        if user.tenant_id is None:

            raise HTTPException(
                status_code=400,
                detail="User is not assigned to any tenant."
            )

    # ----------------------------------------
    # Connect
    # ----------------------------------------

    async def connect(
        self,
        db: Session,
        current_user: User,
        provider: ConnectorProvider,
        token: str
    ):

        self._check_permission(current_user)

        # Get provider implementation
        service = ConnectorFactory.get_service(provider)

        # Validate token and fetch provider details
        provider_data = await service.connect(token)

        # Encrypt token before storing
        encrypted_token = encryption_service.encrypt_token(
            token
        )

        # Existing connector?
        connector = crud.get_connector_by_provider(
            db=db,
            tenant_id=current_user.tenant_id,
            provider=provider
        )

        if connector:

            connector = crud.update_connector(
                db=db,
                connector=connector,
                encrypted_token=encrypted_token,
                account_name=provider_data["account_name"],
                metadata=provider_data["metadata"]
            )

        else:

            connector = crud.create_connector(
                db=db,
                tenant_id=current_user.tenant_id,
                created_by=current_user.id,
                provider=provider,
                encrypted_token=encrypted_token,
                account_name=provider_data["account_name"],
                metadata=provider_data["metadata"]
            )

        return connector

    # ----------------------------------------
    # Disconnect
    # ----------------------------------------

    async def disconnect(
        self,
        db: Session,
        current_user: User,
        provider: ConnectorProvider
    ):

        self._check_permission(current_user)

        connector = crud.get_connector_by_provider(
            db=db,
            tenant_id=current_user.tenant_id,
            provider=provider
        )

        if not connector:

            raise HTTPException(
                status_code=404,
                detail="Connector not found."
            )

        crud.disconnect_connector(
            db=db,
            connector=connector
        )

        return {
            "success": True,
            "message": f"{provider.value} disconnected successfully."
        }

    # ----------------------------------------
    # Get One Connector
    # ----------------------------------------

    async def get_connector(
        self,
        db: Session,
        current_user: User,
        provider: ConnectorProvider
    ):

        self._check_permission(current_user)

        connector = crud.get_connector_by_provider(
            db=db,
            tenant_id=current_user.tenant_id,
            provider=provider
        )

        if not connector:

            raise HTTPException(
                status_code=404,
                detail="Connector not found."
            )

        return connector

    # ----------------------------------------
    # Get All Connectors
    # ----------------------------------------

    async def get_connectors(
        self,
        db: Session,
        current_user: User
    ):

        self._check_permission(current_user)

        return crud.get_connectors(
            db=db,
            tenant_id=current_user.tenant_id
        )


connector_service = ConnectorService()