from typing import Any


class OpenAIProviderService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def _get_client(self, api_key: str | None = None):
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise RuntimeError("The openai SDK is not installed") from exc

        return OpenAI(api_key=api_key or self.api_key)

    def validate_api_key(self, api_key: str) -> bool:
        client = self._get_client(api_key)

        try:
            client.models.list()
            return True
        except Exception as exc:
            raise RuntimeError(f"Invalid OpenAI API key: {exc}") from exc

    def list_models(self, api_key: str | None = None) -> list[dict[str, Any]]:
        client = self._get_client(api_key)
        models = client.models.list()

        return [
            {
                "id": model.id,
                "object": getattr(model, "object", None),
            }
            for model in models.data
        ]

    def generate_completion(
        self,
        api_key: str | None = None,
        prompt: str = "",
        model: str = "gpt-4o-mini",
    ) -> dict[str, Any]:

        client = self._get_client(api_key)

        completion = client.responses.create(
            model=model,
            input=prompt,
            text={
                "format": {
                    "type": "json_object"
                }
            }
        )

        return {
            "id": completion.id,
            "text": completion.output_text,
        }