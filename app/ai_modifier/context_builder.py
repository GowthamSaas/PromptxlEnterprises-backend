from sqlalchemy.orm import Session

from app.projects import crud as project_crud
from app.project_files.service import project_file_service


class AIModifierContextBuilder:
    """
    Builds a lightweight context for AI Modifier.

    Instead of sending the entire project,
    only sends the most relevant files.
    """

    MAX_FILES = 5
    MAX_FILE_CONTENT = 3000

    def build(
        self,
        db: Session,
        project_id: int,
        prompt: str,
    ) -> str:

        context = []

        # -----------------------------
        # Project Details
        # -----------------------------

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

        files = project_file_service.get_project_files(
            db=db,
            project_id=project_id,
        )

        relevant_files = self.select_relevant_files(
            files=files,
            prompt=prompt,
        )

        if relevant_files:

            context.append("\nRelevant Files:\n")

            for file in relevant_files:

                content = file.content or ""

                if len(content) > self.MAX_FILE_CONTENT:
                    content = content[: self.MAX_FILE_CONTENT]

                context.append(
                    f"""
File: {file.file_path}

{content}
"""
                )

        # -----------------------------
        # Current Prompt
        # -----------------------------

        context.append(
            f"\nUser Request:\n{prompt}"
        )

        return "\n".join(context)

    def select_relevant_files(
        self,
        files,
        prompt: str,
    ):

        prompt = prompt.lower()

        scored_files = []

        for file in files:

            score = 0

            path = (file.file_path or "").lower()

            # -----------------------------
            # Prompt Keyword Match
            # -----------------------------

            for word in prompt.split():

                if word in path:
                    score += 5

            # -----------------------------
            # Common Priority Files
            # -----------------------------

            if "router" in path:
                score += 3

            if "app.vue" in path:
                score += 2

            if "main." in path:
                score += 1

            scored_files.append(
                (score, file)
            )

        scored_files.sort(
            key=lambda x: x[0],
            reverse=True,
        )

        return [
            item[1]
            for item in scored_files[: self.MAX_FILES]
        ]


ai_modifier_context_builder = AIModifierContextBuilder()