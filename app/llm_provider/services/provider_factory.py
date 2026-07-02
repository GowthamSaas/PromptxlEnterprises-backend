from app.llm_provider.services.claude_service import ClaudeProviderService
from app.llm_provider.services.gemini_service import GeminiProviderService
from app.llm_provider.services.openai_service import OpenAIProviderService
from app.llm_provider.utils import normalize_provider

_PROVIDER_SERVICES = {
    "openai": OpenAIProviderService,
    "claude": ClaudeProviderService,
    "gemini": GeminiProviderService,
}


def get_provider_service(provider: str, api_key: str | None = None):
    normalized_provider = normalize_provider(provider)
    service_cls = _PROVIDER_SERVICES.get(normalized_provider)
    if service_cls is None:
        supported = ", ".join(_PROVIDER_SERVICES.keys())
        raise ValueError(f"Unsupported provider. Supported values: {supported}")
    return service_cls(api_key=api_key)
