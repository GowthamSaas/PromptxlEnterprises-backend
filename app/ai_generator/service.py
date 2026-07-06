from app.ai_generator.provider_selector import ProviderSelector
from app.ai_generator.prompt_builder import PromptBuilder
from app.ai_generator.response_parser import ResponseParser

from app.ai_generator.services.generation_service import GenerationService
from app.projects import crud as project_crud
from app.project_files.service import project_file_service


class AIGeneratorService:

    def __init__(self):
        self.provider_selector = ProviderSelector()
        self.prompt_builder = PromptBuilder()
        self.generation_service = GenerationService()
        self.response_parser = ResponseParser()

    async def generate(self, db, user, request,):

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

        project = project_crud.create_project(
            db=db,
            user_id=user.id,
            name=parsed_response.get(
                "project_name",
                "Untitled Project",
            ),
            description=parsed_response.get(
                "description",
                None
            ),
            provider=provider.provider,
            model=provider.model,
            status="generated",
        )

        project_file_service.save_project_files(
            db=db,
            project=project,
            files=parsed_response.get(
                "files",
                [],
            ),
        )

        return {
           "success": True,
           "project_id": project.id,
           "project_name": project.name,
           "provider": provider.provider,
           "model": provider.model,
           "response": parsed_response,
        }


ai_generator_service = AIGeneratorService()