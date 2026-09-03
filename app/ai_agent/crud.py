import json

from sqlalchemy.orm import Session

from app.ai_agent.models import (
    AIAgentConnection,
    AIAgentEndpoint,
)

from app.ai_agent.encryption import (
    encrypt_api_token,
)


# ============================================================
# API CONNECTION
# ============================================================


def get_connection(
    db: Session,
    tenant_id: int,
    user_id: int,
):
    return (
        db.query(AIAgentConnection)
        .filter(
            AIAgentConnection.tenant_id == tenant_id,
            AIAgentConnection.connected_by == user_id,
        )
        .first()
    )


def get_connection_by_external_tenant(
    db: Session,
    user_id: int,
    external_tenant: str,
):
    return (
        db.query(AIAgentConnection)
        .filter(
            AIAgentConnection.connected_by == user_id,
            AIAgentConnection.external_tenant == external_tenant,
        )
        .first()
    )


def create_connection(
    db: Session,
    tenant_id: int,
    user_id: int,
    api_token: str,
    external_tenant: str,
):
    connection = AIAgentConnection(
        tenant_id=tenant_id,
        connected_by=user_id,
        encrypted_api_token=encrypt_api_token(
            api_token
        ),
        external_tenant=external_tenant,
    )

    db.add(connection)
    db.commit()
    db.refresh(connection)

    return connection


def update_connection(
    db: Session,
    connection: AIAgentConnection,
    api_token: str | None = None,
    external_tenant: str | None = None,
):
    if api_token:
        connection.encrypted_api_token = (
            encrypt_api_token(api_token)
        )

    if external_tenant:
        connection.external_tenant = external_tenant

    db.commit()
    db.refresh(connection)

    return connection


# ============================================================
# EXTERNAL ENDPOINT
# ============================================================


def get_endpoint(
    db: Session,
    connection_id: int,
    endpoint_id: int,
):
    return (
        db.query(AIAgentEndpoint)
        .filter(
            AIAgentEndpoint.id == endpoint_id,
            AIAgentEndpoint.connection_id == connection_id,
        )
        .first()
    )


def get_endpoints(
    db: Session,
    connection_id: int,
):
    return (
        db.query(AIAgentEndpoint)
        .filter(
            AIAgentEndpoint.connection_id == connection_id
        )
        .order_by(
            AIAgentEndpoint.id.desc()
        )
        .all()
    )


def get_endpoint_by_url(
    db: Session,
    connection_id: int,
    endpoint: str,
):
    return (
        db.query(AIAgentEndpoint)
        .filter(
            AIAgentEndpoint.connection_id == connection_id,
            AIAgentEndpoint.endpoint == endpoint,
        )
        .first()
    )


# ============================================================
# CREATE ENDPOINT
# ============================================================


def create_endpoint(
    db: Session,
    connection_id: int,
    endpoint: str,
    method: str | None = None,
    description: str | None = None,
    resource_name: str | None = None,
    request_schema: dict | None = None,
    response_schema: dict | None = None,
):
    print(f"\n{'='*60}")
    print(f"CRUD create_endpoint - RECEIVED PARAMETERS:")
    print(f"  connection_id: {connection_id}")
    print(f"  endpoint: {endpoint}")
    print(f"  method: {method}")
    print(f"  description: {description}")
    print(f"  resource_name: {resource_name}")
    print(f"  request_schema: {request_schema}")
    print(f"  request_schema TYPE: {type(request_schema)}")
    print(f"  response_schema: {response_schema}")
    print(f"{'='*60}\n")

    db_endpoint = AIAgentEndpoint(
        connection_id=connection_id,
        endpoint=endpoint,
        method=method.upper() if method else "GET",
        description=description,
        resource_name=resource_name,
        request_schema=json.dumps(request_schema) if request_schema else None,
        response_schema=json.dumps(response_schema) if response_schema else None,
    )

    db.add(db_endpoint)
    db.commit()
    db.refresh(db_endpoint)

    print(f"CRUD create_endpoint - AFTER COMMIT:")
    print(f"  db_endpoint.request_schema: {db_endpoint.request_schema}")
    print(f"{'='*60}\n")

    return db_endpoint


# ============================================================
# UPDATE ENDPOINT
# ============================================================


def update_endpoint(
    db: Session,
    endpoint_obj: AIAgentEndpoint,
    endpoint: str | None = None,
    method: str | None = None,
    description: str | None = None,
    resource_name: str | None = None,
    request_schema: dict | None = None,
    response_schema: dict | None = None,
):
    if endpoint is not None:
        endpoint_obj.endpoint = endpoint
    if method is not None:
        endpoint_obj.method = method.upper()
    if description is not None:
        endpoint_obj.description = description
    if resource_name is not None:
        endpoint_obj.resource_name = resource_name
    if request_schema is not None:
        endpoint_obj.request_schema = json.dumps(request_schema) if request_schema else None
    if response_schema is not None:
        endpoint_obj.response_schema = json.dumps(response_schema) if response_schema else None

    db.commit()
    db.refresh(endpoint_obj)

    return endpoint_obj


# ============================================================
# DELETE ENDPOINT
# ============================================================


def delete_endpoint(
    db: Session,
    endpoint_obj: AIAgentEndpoint,
):
    db.delete(endpoint_obj)
    db.commit()

    return True