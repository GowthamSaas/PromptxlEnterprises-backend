from typing import Optional

from sqlalchemy.orm import Session

from app.connectors.models import (
    Connector,
    ConnectorProvider
)


# =====================================================
# Create Connector
# =====================================================

def create_connector(
    db: Session,
    *,
    tenant_id: int,
    created_by: int,
    provider: ConnectorProvider,
    encrypted_token: str,
    account_name: str,
    metadata: dict
) -> Connector:

    connector = Connector(
        tenant_id=tenant_id,
        created_by=created_by,
        provider=provider,
        encrypted_token=encrypted_token,
        account_name=account_name,
        provider_metadata=metadata,
        connected=True
    )

    db.add(connector)
    db.commit()
    db.refresh(connector)

    return connector


# =====================================================
# Get Connector By Provider
# =====================================================

def get_connector_by_provider(
    db: Session,
    *,
    tenant_id: int,
    provider: ConnectorProvider
) -> Optional[Connector]:

    return (
        db.query(Connector)
        .filter(
            Connector.tenant_id == tenant_id,
            Connector.provider == provider
        )
        .first()
    )


# =====================================================
# Get All Connectors
# =====================================================

def get_connectors(
    db: Session,
    *,
    tenant_id: int
):

    return (
        db.query(Connector)
        .filter(
            Connector.tenant_id == tenant_id
        )
        .all()
    )


# =====================================================
# Update Connector
# =====================================================

def update_connector(
    db: Session,
    *,
    connector: Connector,
    encrypted_token: str,
    account_name: str,
    metadata: dict
) -> Connector:

    connector.encrypted_token = encrypted_token
    connector.account_name = account_name
    connector.provider_metadata = metadata
    connector.connected = True
    connector.disconnected_at = None

    db.commit()
    db.refresh(connector)

    return connector


# =====================================================
# Disconnect Connector
# =====================================================

def disconnect_connector(
    db: Session,
    *,
    connector: Connector
) -> Connector:

    connector.connected = False

    db.commit()
    db.refresh(connector)

    return connector


# =====================================================
# Delete Connector
# =====================================================

def delete_connector(
    db: Session,
    *,
    connector: Connector
):

    db.delete(connector)
    db.commit()


# =====================================================
# Is Connected?
# =====================================================

def is_connected(
    db: Session,
    *,
    tenant_id: int,
    provider: ConnectorProvider
) -> bool:

    connector = (
        db.query(Connector)
        .filter(
            Connector.tenant_id == tenant_id,
            Connector.provider == provider,
            Connector.connected == True
        )
        .first()
    )

    return connector is not None