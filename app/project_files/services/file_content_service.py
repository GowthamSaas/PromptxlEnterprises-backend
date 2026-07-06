from sqlalchemy.orm import Session

from app.project_files import crud


class FileContentService:
    """
    Responsible for reading project file content.
    """

    @staticmethod
    def get_file_content(
        db: Session,
        file_id: int,
    ):

        project_file = crud.get_project_file(
            db=db,
            file_id=file_id,
        )

        if project_file is None:
            raise ValueError(
                "Project file not found."
            )

        return project_file


file_content_service = FileContentService()