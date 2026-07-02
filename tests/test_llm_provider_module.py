import unittest

from app.llm_provider.schemas import (
    ConnectProviderRequest,
    DisconnectProviderRequest,
    ProviderResponse,
    ProviderListResponse,
)
from app.llm_provider.utils import get_supported_providers, normalize_provider
from app.llm_provider.provider_factory import get_provider_service


class LLMProviderModuleTest(unittest.TestCase):
    def test_schemas_and_utils(self):
        request = ConnectProviderRequest(provider="openai", api_key="test-key")
        self.assertEqual(request.provider, "openai")
        self.assertEqual(request.api_key, "test-key")

        disconnect = DisconnectProviderRequest(provider="claude")
        self.assertEqual(disconnect.provider, "claude")

        provider = ProviderResponse(id=1, user_id=2, provider="openai")
        self.assertEqual(provider.provider, "openai")

        list_response = ProviderListResponse(providers=[provider], count=1)
        self.assertEqual(list_response.count, 1)

        self.assertIn("openai", get_supported_providers())
        self.assertEqual(normalize_provider("OpenAI"), "openai")

    def test_provider_factory(self):
        service = get_provider_service("gemini")
        self.assertEqual(service.__class__.__name__, "GeminiProviderService")


if __name__ == "__main__":
    unittest.main()
