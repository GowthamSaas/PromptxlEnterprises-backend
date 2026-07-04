from app.llm_provider.service import llm_provider_service


class ProviderSelector:
    """
    Responsible for:

    - Get connected provider
    - Get selected model
    - Decrypt API Key
    - Return provider service
    """

    async def get_provider(
        self,
        user,
        provider: str | None = None,
        model: str | None = None,
    ):
        """
        Returns a configured provider object.
        """

        if not getattr(user, "id", None):
            raise Exception("Authenticated user is required.")

        # Get connected provider from DB
        connected_provider = llm_provider_service.get_connected_provider(
            user_id=user.id,
            provider=provider,
        )

        if not connected_provider:
            raise Exception("No connected provider found.")

        # Decrypt API Key
        api_key = llm_provider_service.decrypt_api_key(
            connected_provider.encrypted_api_key
        )

        # Selected model
        selected_model = (
            model
            or getattr(connected_provider, "selected_model", None)
            or getattr(connected_provider, "default_model", None)
            or self._get_default_model(connected_provider.provider)
        )

        # Provider Service
        provider_service = llm_provider_service.get_provider_service(
            provider=connected_provider.provider,
            api_key=api_key,
        )

        return ProviderContext(
            provider=connected_provider.provider,
            model=selected_model,
            api_key=api_key,
            service=provider_service
        )

    @staticmethod
    def _get_default_model(provider: str | None) -> str:
        defaults = {
            "openai": "gpt-4o-mini",
            "claude": "claude-3-5-sonnet-latest",
            "gemini": "gemini-1.5-flash",
            "minimax": "abab6.5s-chat",
        }
        return defaults.get((provider or "openai").lower(), "gpt-4o-mini")


class ProviderContext:
    """
    AI Generator Provider Context
    """

    def __init__(
        self,
        provider: str,
        model: str,
        api_key: str,
        service,
    ):
        self.provider = provider
        self.model = model
        self.api_key = api_key
        self.service = service