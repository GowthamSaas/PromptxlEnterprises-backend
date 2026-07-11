from sqlalchemy.orm import Session

from app.projects.models import ProjectFile


class ValidationService:
    """
    Responsible for validating
    AI Modifier responses before
    applying file changes.
    """

    VALID_ACTIONS = {
        "create",
        "update",
        "delete",
    }

    VALID_LANGUAGES = {
        "vue",
        "javascript",
        "typescript",
        "html",
        "css",
        "scss",
        "json",
        "python",
        "tsx",
        "jsx",
        "md",
        "txt",
    }

    def validate(
        self,
        db: Session,
        project_id: int,
        files: list,
    ):

        if not isinstance(files, list):
            raise ValueError(
                "Invalid AI response. Files must be a list."
            )

        visited = set()

        for file in files:

            action = file.get("action")

            path = file.get("path")

            language = file.get("language")

            # -----------------------------
            # Validate Action
            # -----------------------------

            if action not in self.VALID_ACTIONS:

                raise ValueError(
                    f"Invalid action '{action}'."
                )

            # -----------------------------
            # Validate Path
            # -----------------------------

            if not path:

                raise ValueError(
                    "File path is required."
                )

            # -----------------------------
            # Duplicate Operations
            # -----------------------------

            key = (action, path)

            if key in visited:

                raise ValueError(
                    f"Duplicate operation detected for '{path}'."
                )

            visited.add(key)

            # -----------------------------
            # Validate Language
            # -----------------------------

            if action != "delete":

                if not language:

                    raise ValueError(
                        f"Language is required for '{path}'."
                    )

                if language not in self.VALID_LANGUAGES:

                    raise ValueError(
                        f"Unsupported language '{language}'."
                    )

            # -----------------------------
            # Existing File Check
            # -----------------------------

            existing_file = (
                db.query(ProjectFile)
                .filter(
                    ProjectFile.project_id == project_id,
                    ProjectFile.file_path == path,
                )
                .first()
            )

            # UPDATE

            if action == "update":

                if not existing_file:

                    raise ValueError(
                        f"Cannot update '{path}'. File does not exist."
                    )

            # CREATE

            elif action == "create":

                if existing_file:

                    raise ValueError(
                        f"Cannot create '{path}'. File already exists."
                    )

            # DELETE

            elif action == "delete":

                if not existing_file:

                    raise ValueError(
                        f"Cannot delete '{path}'. File does not exist."
                    )

        return True


validation_service = ValidationService()