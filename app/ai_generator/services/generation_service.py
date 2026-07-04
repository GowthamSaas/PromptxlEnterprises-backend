class GenerationService:
    """
    Responsible for calling the selected LLM provider.
    """

    async def generate(
        self,
        provider,
        prompt: str,
    ) -> dict:
        """
        Generate AI response.
        """

        response = provider.service.generate_completion(
            api_key=provider.api_key,
            prompt=prompt,
            model=provider.model,
        )

        return response