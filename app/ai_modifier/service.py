from sqlalchemy.orm import Session

from app.ai_chat.context_builder import (
    context_builder,
)

from app.ai_generator.provider_selector import (
    ProviderSelector,
)

from app.ai_generator.services.generation_service import (
    GenerationService,
)

from app.ai_modifier.response_parser import (
    response_parser,
)

from app.ai_modifier.file_update_service import (
    file_update_service,
)

from app.ai_modifier.diff_service import (
    diff_service,
)


class AIModifierService:

    def __init__(self):

        self.provider_selector = ProviderSelector()

        self.generation_service = GenerationService()

    async def modify(
        self,
        db: Session,
        user,
        request,
    ):

        # ----------------------------------
        # Select Provider
        # ----------------------------------

        provider = await self.provider_selector.get_provider(
            user=user,
            provider=request.provider,
            model=request.model,
        )

        # ----------------------------------
        # Build Context
        # ----------------------------------

        context = context_builder.build(
            db=db,
            project_id=request.project_id,
            session_id=None,
            prompt=request.prompt,
        )

        # ----------------------------------
        # AI Modifier Prompt
        # ----------------------------------

        final_prompt = f"""
You are an expert Full Stack Software Engineer.

Modify ONLY the requested files.

Do NOT regenerate the complete project.

Return ONLY JSON.

Expected format:

{{
    "message":"...",
    "files":[
        {{
            "action":"update",
            "path":"src/App.vue",
            "language":"vue",
            "content":"..."
        }}
    ]
}}

User Request:

{request.prompt}

Current Project:

{context}
"""

        # ----------------------------------
        # Generate Response
        # ----------------------------------

        response = await self.generation_service.generate(
            provider=provider,
            prompt=final_prompt,
        )

        # ----------------------------------
        # Parse Response
        # ----------------------------------

        parsed = response_parser.parse(
            response
        )

        modified_files = parsed.get(
            "files",
            [],
        )

        # ----------------------------------
        # Generate Diff
        # ----------------------------------

        for file in modified_files:

            file["diff"] = ""

        # ----------------------------------
        # Update Project Files
        # ----------------------------------

        updated_files = (
            file_update_service.apply_changes(
                db=db,
                project_id=request.project_id,
                modified_files=modified_files,
            )
        )

        # ----------------------------------
        # Response
        # ----------------------------------

        return {

            "success": True,

            "message": parsed.get(
                "message",
                "Project updated successfully.",
            ),

            "modified_files": updated_files,

        }


ai_modifier_service = AIModifierService()