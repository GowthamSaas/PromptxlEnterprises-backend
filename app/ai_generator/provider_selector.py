from typing import Any

from .constants import DEFAULT_PROVIDER, SUPPORTED_PROVIDERS


def select_provider(preferred_provider: str | None = None) -> str:
    provider = (preferred_provider or DEFAULT_PROVIDER).strip().lower()
    if provider not in SUPPORTED_PROVIDERS:
        return DEFAULT_PROVIDER
    return provider


def build_provider_payload(provider: str, prompt: str) -> dict[str, Any]:
    return {
        "provider": provider,
        "prompt": prompt,
    }
