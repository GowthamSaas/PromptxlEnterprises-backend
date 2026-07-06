from pathlib import PurePath

from app.projects.constants import MAX_PROJECT_NAME_LENGTH


class ProjectValidator:

    @staticmethod
    def validate_project_name(name: str) -> None:

        if not name:
            raise ValueError(
                "Project name is required."
            )

        if len(name) > MAX_PROJECT_NAME_LENGTH:
            raise ValueError(
                f"Project name cannot exceed {MAX_PROJECT_NAME_LENGTH} characters."
            )

  