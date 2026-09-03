from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.auth.dependencies import (
    get_current_user,
)

from app.ai_agent.encryption import (
    decrypt_api_token,
)

from app.ai_agent import service

from app.ai_agent.schemas import (
    AIAgentConnectRequest,
    AIAgentConnectionResponse,
    AIAgentUpdateRequest,
    AIAgentEndpointCreate,
    AIAgentEndpointResponse,
    AIAgentEndpointUpdate,
    AIAgentEndpointDeleteResponse,
    AIAgentPromptRequest,
    AIAgentPromptResponse,
)


router = APIRouter()


# ============================================================
# API CONNECTION
# ============================================================


@router.post(
    "/connect",
    response_model=AIAgentConnectionResponse,
)
def connect_api(
    payload: AIAgentConnectRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    try:

        connection = service.connect_api(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            api_token=payload.api_token,
            external_tenant=payload.external_tenant,
        )

        return {
            "id": connection.id,
            "connected": True,
            "external_tenant": connection.external_tenant,
            "created_at": connection.created_at,
            "updated_at": connection.updated_at,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# GET CONNECTION
# ============================================================


@router.get(
    "/connection",
    response_model=AIAgentConnectionResponse,
)
def get_connection(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    try:

        connection = service.get_api_connection(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
        )

        if not connection:

            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="API connection not found.",
            )

        return {
            "id": connection.id,
            "connected": True,
            "external_tenant": connection.external_tenant,
            "api_token": decrypt_api_token(
                connection.encrypted_api_token
            ),
            "created_at": connection.created_at,
            "updated_at": connection.updated_at,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# UPDATE CONNECTION
# ============================================================


@router.put(
    "/connection",
    response_model=AIAgentConnectionResponse,
)
def update_connection(
    payload: AIAgentUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    try:

        connection = service.update_api_connection(
            db=db,
            user_id=current_user.id,
            tenant_id=current_user.tenant_id,
            api_token=payload.api_token,
            external_tenant=payload.external_tenant,
        )

        return {
            "id": connection.id,
            "connected": True,
            "external_tenant": connection.external_tenant,
            "created_at": connection.created_at,
            "updated_at": connection.updated_at,
        }

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# CONNECT ENDPOINT
# ============================================================


@router.post(
    "/endpoint",
    response_model=AIAgentEndpointResponse,
    status_code=status.HTTP_201_CREATED,
)
def connect_endpoint(
    payload: AIAgentEndpointCreate,
    tenant: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    print(f"\n{'='*60}")
    print(f"ROUTER connect_endpoint - payload.request_schema: {payload.request_schema}")
    print(f"ROUTER connect_endpoint - payload.request_schema TYPE: {type(payload.request_schema)}")
    print(f"ROUTER connect_endpoint - payload: {payload}")
    print(f"{'='*60}\n")

    try:

        return service.connect_endpoint(
            db=db,
            user_id=current_user.id,
            external_tenant=tenant,
            endpoint=payload.endpoint,
            method=payload.method,
            description=payload.description,
            resource_name=payload.resource_name,
            request_schema=payload.request_schema,
            response_schema=payload.response_schema,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# GET ENDPOINTS
# ============================================================


@router.get(
    "/endpoints",
    response_model=list[AIAgentEndpointResponse],
)
def get_endpoints(
    tenant: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    try:

        return service.get_connected_endpoints(
            db=db,
            user_id=current_user.id,
            external_tenant=tenant,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# UPDATE ENDPOINT
# ============================================================


@router.put(
    "/endpoint/{endpoint_id}",
    response_model=AIAgentEndpointResponse,
)
def update_endpoint(
    endpoint_id: int,
    payload: AIAgentEndpointUpdate,
    tenant: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    try:

        return service.update_connected_endpoint(
            db=db,
            user_id=current_user.id,
            external_tenant=tenant,
            endpoint_id=endpoint_id,
            endpoint=payload.endpoint,
            method=payload.method,
            description=payload.description,
            resource_name=payload.resource_name,
            request_schema=payload.request_schema,
            response_schema=payload.response_schema,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# DELETE ENDPOINT
# ============================================================


@router.delete(
    "/endpoint/{endpoint_id}",
    response_model=AIAgentEndpointDeleteResponse,
)
def delete_endpoint(
    endpoint_id: int,
    tenant: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    try:

        return service.delete_connected_endpoint(
            db=db,
            user_id=current_user.id,
            external_tenant=tenant,
            endpoint_id=endpoint_id,
        )

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


# ============================================================
# AI AGENT PROMPT
# ============================================================


@router.post(
    "/prompt",
    response_model=AIAgentPromptResponse,
    status_code=status.HTTP_200_OK,
)
async def execute_prompt(
    payload: AIAgentPromptRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    try:

        print("\n========== AI AGENT ROUTER DEBUG ==========")
        print("PROMPT:", payload.prompt)
        print("METHOD:", payload.method)
        print("REQUEST BODY:", payload.request_body)
        print("CONVERSATION HISTORY:", payload.conversation_history)
        print(
           "HISTORY COUNT:",
            len(payload.conversation_history or [])
        )
        print("===========================================\n")

        result = await service.process_prompt(
            db=db,
            user=current_user,

            # Current user message
            prompt=payload.prompt,

            # Connected endpoint
            endpoint_id=payload.endpoint_id,

            # Direct endpoint
            endpoint=payload.endpoint,

            # External tenant
            external_tenant=payload.external_tenant,

            # LLM
            provider=payload.provider,
            model=payload.model,

            # Previous response
            previous_output=payload.previous_output,

            # Explicit HTTP method if provided
            method=payload.method,

            # Optional frontend request body
            request_body=payload.request_body,

            # IMPORTANT:
            # Full previous conversation
            conversation_history=payload.conversation_history,
        )

        return result

    except ValueError as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        )