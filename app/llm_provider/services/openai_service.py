from typing import Any


class OpenAIProviderService:
    # Models intentionally available in the application builder.  The OpenAI
    # models endpoint also includes audio, image, moderation, legacy, and other
    # non-coding models that cannot be used for this workflow.
    APP_BUILDER_MODEL_IDS = (
        "gpt-5.6-sol",
        "gpt-5.6-terra",
        "gpt-5.6-luna",
        "gpt-5.5-pro",
        "gpt-5.5",
        "gpt-5.4-pro",
        "gpt-5.4",
        "gpt-5-codex",
        "gpt-5.2-codex",
        "gpt-5.3-codex",
        "gpt-5.4-mini",
        "gpt-5.4-nano",
    )

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
        available_models = {
            model.id: model
            for model in models.data
            if model.id in self.APP_BUILDER_MODEL_IDS
        }

        return [
            {
                "id": model_id,
                "object": getattr(model, "object", None),
            }
            for model_id in self.APP_BUILDER_MODEL_IDS
            if (model := available_models.get(model_id)) is not None
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