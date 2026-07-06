from pathlib import PurePath


class ProjectFileValidator:

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