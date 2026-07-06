from sqlalchemy.orm import Session

from app.project_files import crud
from app.project_files.exceptions import (
    ProjectFileNotFoundException,
)


class FileDeleteService:
    """
    Responsible for deleting a project file.
    """

    @staticmethod
    def delete_file(
        db: Session,
        file_id: int,
    ):

        project_file = crud.get_project_file(
            db=db,
            file_id=file_id,
        )

        if project_file is None:
            raise ProjectFileNotFoundException(
                "Project file not found."
            )

        crud.delete_project_file(
            db=db,
            project_file=project_file,
        )

        return {
            "message": "Project file deleted successfully."
        }


file_delete_service = FileDeleteService()