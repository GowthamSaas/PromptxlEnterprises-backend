from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user, require_owner, require_admin_or_owner
from app.database import get_db
from app.llm_provider.schemas import (
    ConnectProviderRequest,
    DisconnectProviderRequest,
    ProviderListResponse,
    ProviderResponse,
)
from app.llm_provider.service import LLMProviderService
from app.llm_provider.utils import (
    build_provider_list_response,
    build_provider_response,
)
from app.models.user import User, UserRole
from app.models.tenant import Tenant

router = APIRouter()


@router.post(
    "/connect",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
)
def connect_provider_endpoint(
    payload: ConnectProviderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
) -> ProviderResponse:
    """
    Connect a new LLM Provider (Owner only)
    """

    try:
        provider_record = LLMProviderService.connect_provider(
            db=db,
            user_id=current_user.id,
            provider=payload.provider,
            api_key=payload.api_key,
        )

        return build_provider_response(provider_record)

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )


@router.post(
    "/disconnect",
    status_code=status.HTTP_204_NO_CONTENT,
)
def disconnect_provider_endpoint(
    payload: DisconnectProviderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_owner),
):
    """
    Disconnect Provider (Owner only)
    """

    removed = LLMProviderService.disconnect_provider(
        db=db,
        user_id=current_user.id,
        provider=payload.provider,
    )

    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Provider connection not found",
        )


@router.get(
    "/providers",
    response_model=ProviderListResponse,
)
def list_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner),
):
    """
    Get Connected Providers (Admin/Owner only)
    """

    # Check if user is owner (role can be string or enum)
    is_owner = current_user.role == UserRole.OWNER or current_user.role == "owner"
    
    if is_owner:
        user_id = current_user.id
    else:
        # If admin, get owner's providers from tenant
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if not tenant or not tenant.created_by:
            return build_provider_list_response([])
        user_id = tenant.created_by
    
    providers = LLMProviderService.get_connected_providers(
        db=db,
        user_id=user_id,
    )

    return build_provider_list_response(providers)


@router.get("/models/{provider}")
def list_provider_models(
    provider: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin_or_owner),
) -> dict[str, Any]:
    """
    Get Models for Connected Provider (Admin/Owner only)
    """

    # Check if user is owner (role can be string or enum)
    is_owner = current_user.role == UserRole.OWNER or current_user.role == "owner"
    
    if is_owner:
        user_id = current_user.id
    else:
        # If admin, get owner's providers from tenant
        tenant = db.query(Tenant).filter(Tenant.id == current_user.tenant_id).first()
        if not tenant or not tenant.created_by:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tenant or owner not found"
            )
        user_id = tenant.created_by

    try:
        models = LLMProviderService.get_provider_models(
            db=db,
            user_id=user_id,
            provider=provider,
        )

        return {
            "provider": provider,
            "models": models,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )

    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )