from sqlalchemy.orm import Session

from app.project_files import crud
from app.project_files.exceptions import (
    ProjectFileNotFoundException,
)


class FileSaveService:
    """
    Responsible for saving file content.
    """

    @staticmethod
    def save_file(
        db: Session,
        file_id: int,
        content: str,
    ):

        project_file = crud.get_project_file(
            db=db,
            file_id=file_id,
        )

        if project_file is None:
            raise ProjectFileNotFoundException(
                "Project file not found."
            )

        return crud.update_project_file(
            db=db,
            project_file=project_file,
            content=content,
        )


file_save_service = FileSaveService()