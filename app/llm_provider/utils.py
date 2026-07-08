from typing import Any

from app.llm_provider.schemas import ProviderListResponse, ProviderResponse

SUPPORTED_PROVIDERS = ("openai", "claude", "gemini" , "minimax")
PROVIDER_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "claude": "Anthropic Claude",
    "gemini": "Google Gemini",
    "minimax": "Minimax",
}


def normalize_provider(provider: str) -> str:
    return provider.strip().lower()


def validate_provider_name(provider: str) -> str:
    normalized = normalize_provider(provider)
    if normalized not in SUPPORTED_PROVIDERS:
        supported = ", ".join(SUPPORTED_PROVIDERS)
        raise ValueError(f"Unsupported provider. Supported values: {supported}")
    return normalized


def get_supported_providers() -> tuple[str, ...]:
    return SUPPORTED_PROVIDERS


def build_provider_response(provider_record: Any) -> ProviderResponse:
    return ProviderResponse(
        id=provider_record.id,
        tenant_id=provider_record.tenant_id,
        connected_by_id=provider_record.connected_by,
        provider=provider_record.provider,
        validated_at=provider_record.validated_at,
        created_at=provider_record.created_at,
        updated_at=provider_record.updated_at,

        # -------- Admin UI --------
        owner_connected=True,
        connected_by=provider_record.connected_user.full_name,
        connected_on=provider_record.created_at,
        last_used=provider_record.updated_at,
    )


def build_provider_list_response(provider_records: list[Any]) -> ProviderListResponse:
    providers = [build_provider_response(record) for record in provider_records]
    return ProviderListResponse(providers=providers, count=len(providers))
