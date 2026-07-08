from sqlalchemy.orm import Session

from app.ai_chat.context_builder import (
    context_builder,
)

from app.ai_chat.conversation_service import (
    conversation_service,
)

from app.ai_generator.provider_selector import (
    ProviderSelector,
)

from app.ai_generator.services.generation_service import (
    GenerationService,
)
from app.ai_chat.response_parser import (
    response_parser,
)


class AIChatService:

    def __init__(self):

        self.provider_selector = ProviderSelector()

        self.generation_service = GenerationService()

    async def chat(
        self,
        db: Session,
        user,
        request,
    ):

      
        # ----------------------------------
# Create / Reuse Chat Session
# ----------------------------------

        if request.session_id:

            session = conversation_service.get_session(
               db=db,
               session_id=request.session_id,
            )

            if not session:
                raise ValueError("Chat session not found")

        else:

            session = conversation_service.create_session(
                db=db,
                user_id=user.id,
                project_id=request.project_id,
                title=request.prompt[:50],
            )

        # ----------------------------------
        # Save User Message
        # ----------------------------------

        conversation_service.save_message(
            db=db,
            session_id=session.id,
            role="user",
            message=request.prompt,
        )

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
            session_id=session.id,
            prompt=request.prompt,
        )

        # ----------------------------------
        # Generate AI Response
        # ----------------------------------

        response = await self.generation_service.generate(
            provider=provider,
            prompt=context,
        )

        assistant_message = response_parser.parse(
            response
        )

        conversation_service.save_message(
           db=db,
           session_id=session.id,
           role="assistant",
           message=assistant_message,
        )

        # ----------------------------------
        # Response
        # ----------------------------------

        return {
           "success": True,
           "session_id": session.id,
           "message": assistant_message,
           "created_at": session.created_at,
        }


    def get_chat_history(
        self,
        db: Session,
        session_id: int,
    ):

        return conversation_service.get_session_messages(
            db=db,
            session_id=session_id,
        )


    def get_chat_sessions(
        self,
        db: Session,
        user,
    ):

        return conversation_service.get_user_sessions(
            db=db,
            user_id=user.id,
        )


    def delete_chat_session(
        self,
        db: Session,
        session_id: int,
    ):

        return conversation_service.delete_session(
           db=db,
           session_id=session_id,
        )

    


ai_chat_service = AIChatService()