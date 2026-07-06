from sqlalchemy.orm import Session

from app.project_files import crud
from app.project_files.exceptions import (
    ProjectFileAlreadyExistsException,
)


class FileCreateService:
    """
    Responsible for creating a new file.
    """

    @staticmethod
    def create_file(
        db: Session,
        project_id: int,
        file_name: str,
        file_path: str,
        language: str | None = None,
        content: str = "",
    ):

        # Check duplicate file
        existing_files = crud.get_project_files(
            db=db,
            project_id=project_id,
        )

        for file in existing_files:
            if file.file_path == file_path:
                raise ProjectFileAlreadyExistsException(
                    "File already exists."
                )

        return crud.create_project_file(
            db=db,
            project_id=project_id,
            file_name=file_name,
            file_path=file_path,
            language=language,
            content=content,
        )


file_create_service = FileCreateService()