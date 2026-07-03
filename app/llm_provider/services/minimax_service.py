# from typing import Any

# import httpx


# class MiniMaxProviderService:
#     BASE_URL = "https://api.minimax.chat/v1"

#     def __init__(self, api_key: str | None = None):
#         self.api_key = api_key

#     def _headers(self, api_key: str | None = None):
#         return {
#             "Authorization": f"Bearer {api_key or self.api_key}",
#             "Content-Type": "application/json",
#         }

#     def validate_api_key(self, api_key: str) -> bool:
#         """
#         Validate MiniMax API key by listing models.
#         """

#         try:
#             response = httpx.get(
#                 f"{self.BASE_URL}/models",
#                 headers=self._headers(api_key),
#                 timeout=20,
#             )

#             if response.status_code == 200:
#                 return True

#             raise RuntimeError(response.text)

#         except Exception as exc:
#             raise RuntimeError(f"Invalid MiniMax API key: {exc}") from exc

#     def list_models(self, api_key: str | None = None) -> list[dict[str, Any]]:
#         response = httpx.get(
#             f"{self.BASE_URL}/models",
#             headers=self._headers(api_key),
#             timeout=20,
#         )

#         response.raise_for_status()

#         data = response.json()

#         return [
#             {
#                 "name": model["id"]
#             }
#             for model in data.get("data", [])
#         ]

#     def generate_completion(
#         self,
#         api_key: str | None = None,
#         prompt: str = "",
#         model: str = "MiniMax-M1",
#     ) -> dict[str, Any]:

#         payload = {
#             "model": model,
#             "messages": [
#                 {
#                     "role": "user",
#                     "content": prompt,
#                 }
#             ],
#         }

#         response = httpx.post(
#             f"{self.BASE_URL}/text/chatcompletion_v2",
#             headers=self._headers(api_key),
#             json=payload,
#             timeout=60,
#         )

#         response.raise_for_status()

#         data = response.json()

#         return {
#             "text": data["choices"][0]["message"]["content"]
#         }



from typing import Any

from openai import OpenAI


class MiniMaxProviderService:
    def __init__(self, api_key: str | None = None):
        self.api_key = api_key

    def _get_client(self, api_key: str | None = None):
        try:
            return OpenAI(
                api_key=api_key or self.api_key,
                base_url="https://api.minimax.io/v1",
            )
        except Exception as exc:
            raise RuntimeError("Failed to initialize MiniMax client") from exc

    def validate_api_key(self, api_key: str) -> bool:
        client = self._get_client(api_key)

        try:
            client.models.list()
            return True
        except Exception as exc:
            raise RuntimeError(f"Invalid MiniMax API key: {exc}") from exc

    def list_models(self, api_key: str | None = None) -> list[dict[str, Any]]:
        client = self._get_client(api_key)

        try:
            models = client.models.list()

            return [
                {
                    "id": model.id,
                    "object": getattr(model, "object", None),
                }
                for model in models.data
            ]

        except Exception as exc:
            raise RuntimeError(f"Unable to fetch MiniMax models: {exc}") from exc

    def generate_completion(
        self,
        api_key: str | None = None,
        prompt: str = "",
        model: str = "MiniMax-M1",
    ) -> dict[str, Any]:

        client = self._get_client(api_key)

        try:
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                temperature=0.7,
            )

            return {
                "id": completion.id,
                "text": completion.choices[0].message.content,
            }

        except Exception as exc:
            raise RuntimeError(f"MiniMax generation failed: {exc}") from exc