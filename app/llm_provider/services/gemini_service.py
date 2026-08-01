from typing import Any


class GeminiProviderService:
    APP_BUILDER_MODEL_IDS = (
        "gemini-3.1-pro-preview",
        "gemini-3-pro-preview",
        "gemini-2.5-pro",
        "gemini-3.6-flash",
        "gemini-3.5-flash",
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-2.5-flash-lite",
        "gemini-3.5-flash-lite",
        "gemini-3.1-flash-lite",
        "gemini-flash-lite-latest",
        "gemini-2.0-flash-lite",
    )

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def _get_client(self, api_key: str | None = None):
        try:
            import google.generativeai as genai
        except ImportError as exc:
            raise RuntimeError(
                "The google-generativeai SDK is not installed"
            ) from exc

        genai.configure(api_key=api_key or self.api_key)
        return genai

    def validate_api_key(self, api_key: str) -> bool:
        try:
            genai = self._get_client(api_key)

            models = list(genai.list_models())

            if not models:
                raise RuntimeError("No models found")

            return True

        except Exception as exc:
            raise RuntimeError(
                f"Invalid Gemini API key: {exc}"
            ) from exc

    def list_models(
        self,
        api_key: str | None = None,
    ) -> list[dict[str, Any]]:

        return [
            {"id": model_id}
            for model_id in self.APP_BUILDER_MODEL_IDS
        ]

    def generate_completion(
        self,
        api_key: str | None = None,
        prompt: str = "",
        model: str = "gemini-3.1-pro-preview",
    ) -> dict[str, Any]:

        genai = self._get_client(api_key)

        model_client = genai.GenerativeModel(
            model_name=model
        )

        response = model_client.generate_content(
            prompt,
            generation_config={
                "temperature": 0.2,
            },
        )

        return {
            "text": response.text
        }
