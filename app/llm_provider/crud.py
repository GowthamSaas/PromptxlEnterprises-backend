from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from app.llm_provider.models import LLMProvider
from app.llm_provider.utils import normalize_provider


def connect_provider(
    db: Session,
    user_id: int,
    provider: str,
    encrypted_api_key: str,
) -> LLMProvider:

    normalized_provider = normalize_provider(provider)

    existing = (
        db.query(LLMProvider)
        .filter(
            LLMProvider.user_id == user_id,
            LLMProvider.provider == normalized_provider,
        )
        .first()
    )

    if existing is None:
        provider_record = LLMProvider(
            user_id=user_id,
            provider=normalized_provider,
            encrypted_api_key=encrypted_api_key,
            validated_at=datetime.now(timezone.utc),
        )

        db.add(provider_record)
        db.commit()
        db.refresh(provider_record)

        return provider_record

    existing.encrypted_api_key = encrypted_api_key
    existing.validated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(existing)

    return existing


def disconnect_provider(
    db: Session,
    user_id: int,
    provider: str,
) -> bool:

    normalized_provider = normalize_provider(provider)

    provider_record = (
        db.query(LLMProvider)
        .filter(
            LLMProvider.user_id == user_id,
            LLMProvider.provider == normalized_provider,
        )
        .first()
    )

    if provider_record is None:
        return False

    db.delete(provider_record)
    db.commit()

    return True


def get_user_provider(
    db: Session,
    user_id: int,
    provider: str,
) -> Optional[LLMProvider]:

    normalized_provider = normalize_provider(provider)

    return (
        db.query(LLMProvider)
        .filter(
            LLMProvider.user_id == user_id,
            LLMProvider.provider == normalized_provider,
        )
        .first()
    )


def get_all_user_providers(
    db: Session,
    user_id: int,
) -> list[LLMProvider]:

    return (
        db.query(LLMProvider)
        .filter(LLMProvider.user_id == user_id)
        .order_by(LLMProvider.provider)
        .all()
    )


def update_provider(
    db: Session,
    provider_record: LLMProvider,
    encrypted_api_key: str,
) -> LLMProvider:

    provider_record.encrypted_api_key = encrypted_api_key
    provider_record.validated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(provider_record)

    return provider_record