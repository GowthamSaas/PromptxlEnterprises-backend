class AIGenerationError(Exception):
    """Raised when the AI generation workflow fails."""


class ProviderUnavailableError(AIGenerationError):
    """Raised when the configured provider is unavailable."""


class InvalidGenerationResponseError(AIGenerationError):
    """Raised when the model returns an unusable response."""
