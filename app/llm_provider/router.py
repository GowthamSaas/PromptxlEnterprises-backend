from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
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
from app.models.user import User

router = APIRouter()


@router.post(
    "/connect",
    response_model=ProviderResponse,
    status_code=status.HTTP_201_CREATED,
)
def connect_provider_endpoint(
    payload: ConnectProviderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProviderResponse:
    """
    Connect a new LLM Provider
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
    current_user: User = Depends(get_current_user),
):
    """
    Disconnect Provider
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
    current_user: User = Depends(get_current_user),
):
    """
    Get Connected Providers
    """

    providers = LLMProviderService.get_connected_providers(
        db=db,
        user_id=current_user.id,
    )

    return build_provider_list_response(providers)


@router.get("/models/{provider}")
def list_provider_models(
    provider: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    """
    Get Models for Connected Provider
    """

    try:
        models = LLMProviderService.get_provider_models(
            db=db,
            user_id=current_user.id,
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