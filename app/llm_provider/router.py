from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.llm_provider.crud import connect_provider, disconnect_provider, get_all_user_providers
from app.llm_provider.schemas import ConnectProviderRequest, DisconnectProviderRequest, ProviderListResponse, ProviderResponse
from app.llm_provider.services.provider_factory import get_provider_service
from app.llm_provider.utils import build_provider_list_response, build_provider_response, validate_provider_name
from app.models.user import User

router = APIRouter()


@router.post("/connect", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
def connect_provider_endpoint(
    payload: ConnectProviderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProviderResponse:
    provider_name = validate_provider_name(payload.provider)
    service = get_provider_service(provider_name)

    try:
        service.validate_api_key(payload.api_key)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    stored_provider = connect_provider(db, current_user.id, provider_name, payload.api_key)
    return build_provider_response(stored_provider)


@router.post("/disconnect", status_code=status.HTTP_204_NO_CONTENT)
def disconnect_provider_endpoint(
    payload: DisconnectProviderRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    provider_name = validate_provider_name(payload.provider)
    removed = disconnect_provider(db, current_user.id, provider_name)
    if not removed:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Provider connection not found")


@router.get("/providers", response_model=ProviderListResponse)
def list_providers(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProviderListResponse:
    provider_records = get_all_user_providers(db, current_user.id)
    return build_provider_list_response(provider_records)


@router.get("/models/{provider}")
def list_provider_models(
    provider: str,
    current_user: User = Depends(get_current_user),
) -> dict[str, Any]:
    provider_name = validate_provider_name(provider)
    service = get_provider_service(provider_name)

    try:
        models = service.list_models("")
    except RuntimeError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc)) from exc

    return {"provider": provider_name, "models": models}
