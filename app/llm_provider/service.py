from sqlalchemy.orm import Session

from app.llm_provider import crud
from app.llm_provider.models import LLMProvider
from app.llm_provider.services.encryption_service import (
    decrypt_api_key,
    encrypt_api_key,
)
from app.llm_provider.services.provider_factory import get_provider_service


class LLMProviderService:

    @staticmethod
    def connect_provider(
        db: Session,
        user_id: int,
        provider: str,
        api_key: str,
    ) -> LLMProvider:

        provider_service = get_provider_service(provider)

        # Validate API Key
        provider_service.validate_api_key(api_key)

        # Encrypt API Key
        encrypted_key = encrypt_api_key(api_key)

        # Save Database
        provider_record = crud.connect_provider(
            db=db,
            user_id=user_id,
            provider=provider,
            encrypted_api_key=encrypted_key,
        )

        return provider_record

    @staticmethod
    def disconnect_provider(
        db: Session,
        user_id: int,
        provider: str,
    ) -> bool:

        return crud.disconnect_provider(
            db=db,
            user_id=user_id,
            provider=provider,
        )

    @staticmethod
    def get_connected_providers(
        db: Session,
        user_id: int,
    ):

        return crud.get_all_user_providers(
            db=db,
            user_id=user_id,
        )

    @staticmethod
    def get_provider_models(
        db: Session,
        user_id: int,
        provider: str,
    ):

        provider_record = crud.get_user_provider(
            db=db,
            user_id=user_id,
            provider=provider,
        )

        if provider_record is None:
            raise ValueError(
                f"{provider} provider is not connected."
            )

        api_key = decrypt_api_key(
            provider_record.encrypted_api_key
        )

        provider_service = get_provider_service(
            provider,
            api_key,
        )

        return provider_service.list_models(api_key)