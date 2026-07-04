from app.ai_generator.provider_selector import ProviderSelector
from app.ai_generator.prompt_builder import PromptBuilder
from app.ai_generator.response_parser import ResponseParser

from app.ai_generator.services.generation_service import GenerationService


class AIGeneratorService:

    def __init__(self):
        self.provider_selector = ProviderSelector()
        self.prompt_builder = PromptBuilder()
        self.generation_service = GenerationService()
        self.response_parser = ResponseParser()

    async def generate(self, user, request):

        # Get connected provider and API key
        provider = await self.provider_selector.get_provider(
            user=user,
            provider=request.provider,
            model=request.model
        )

        # Build final prompt
        prompt = self.prompt_builder.build(
            prompt=request.prompt
        )

        # Generate AI response
        response = await self.generation_service.generate(
            provider=provider,
            prompt=prompt
        )

        # Parse response
        parsed_response = self.response_parser.parse(
            response=response
        )

        return {
            "success": True,
            "provider": provider.provider,
            "model": provider.model,
            "response": parsed_response
        }


ai_generator_service = AIGeneratorService()