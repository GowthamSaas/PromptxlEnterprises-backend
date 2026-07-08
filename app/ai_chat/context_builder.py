from sqlalchemy.orm import Session

from app.projects import crud as project_crud
from app.project_files.service import project_file_service

from app.ai_chat.conversation_service import (
    conversation_service,
)


class ContextBuilder:
    """
    Responsible for building
    project and conversation context
    for the AI Chat.
    """

    def build(
        self,
        db: Session,
        project_id: int | None,
        session_id: int | None,
        prompt: str,
    ) -> str:

        context = []

        # -----------------------------
        # Project Details
        # -----------------------------

        if project_id:

            project = project_crud.get_project(
                db=db,
                project_id=project_id,
            )

            if project:

                context.append(
                    f"Project Name: {project.name}"
                )

                if project.description:

                    context.append(
                        f"Description: {project.description}"
                    )

        # -----------------------------
        # Project Files
        # -----------------------------

        if project_id:

            files = (
                project_file_service.get_project_files(
                    db=db,
                    project_id=project_id,
                )
            )

            if files:

                context.append("\nProject Files:\n")

                for file in files:

                    context.append(
                        f"""
File: {file.file_path}

{file.content}
"""
                    )

        # -----------------------------
        # Conversation History
        # -----------------------------

        if session_id:

            messages = (
                conversation_service.get_messages(
                    db=db,
                    session_id=session_id,
                )
            )

            if messages:

                context.append(
                    "\nConversation History:\n"
                )

                for message in messages:

                    context.append(
                        f"{message.role}: {message.message}"
                    )

        # -----------------------------
        # Current Prompt
        # -----------------------------

        context.append(
            f"\nUser Request:\n{prompt}"
        )

        return "\n".join(context)


context_builder = ContextBuilder()