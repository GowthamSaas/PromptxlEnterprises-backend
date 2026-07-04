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

    @staticmethod
    def validate_files(files: list[dict]) -> None:

        if not files:
            raise ValueError(
                "Project files cannot be empty."
            )

        for file in files:

            if "path" not in file:
                raise ValueError(
                    "File path is required."
                )

            if "content" not in file:
                raise ValueError(
                    "File content is required."
                )

            PurePath(file["path"])