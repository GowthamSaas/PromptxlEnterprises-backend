from typing import Any


class ClaudeProviderService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def _get_client(self, api_key: str | None = None):
        try:
            from anthropic import Anthropic
        except ImportError as exc:  # pragma: no cover - depends on environment
            raise RuntimeError("The anthropic SDK is not installed") from exc

        return Anthropic(api_key=api_key or self.api_key)

    def validate_api_key(self, api_key: str) -> bool:
        client = self._get_client(api_key)
        try:
            client.models.list()
            return True
        except Exception as exc:  # pragma: no cover - SDK may raise various errors
            raise RuntimeError(f"Invalid Claude API key: {exc}") from exc

    def list_models(self, api_key: str | None = None) -> list[dict[str, Any]]:
        client = self._get_client(api_key)
        models = client.models.list()
        return [{"id": model.id} for model in models.data]

    def generate_completion(self, api_key: str | None = None, prompt: str = "", model: str = "claude-3-5-sonnet-latest") -> dict[str, Any]:
        client = self._get_client(api_key)
        message = client.messages.create(model=model, max_tokens=256, messages=[{"role": "user", "content": prompt}])
        return {"id": message.id, "text": message.content[0].text}
