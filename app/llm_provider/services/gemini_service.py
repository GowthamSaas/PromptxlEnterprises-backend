from typing import Any


class GeminiProviderService:
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

        genai = self._get_client(api_key)

        models = genai.list_models()

        return [
            {"name": model.name}
            for model in models
        ]

    def generate_completion(
        self,
        api_key: str | None = None,
        prompt: str = "",
        model: str = "gemini-1.5-flash",
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