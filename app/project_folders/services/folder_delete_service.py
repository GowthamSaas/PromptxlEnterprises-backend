from sqlalchemy.orm import Session

from app.project_folders import crud


class FolderDeleteService:
    @staticmethod
    def delete_folder(
        db: Session,
        folder_id: int,
    ):

        folder = crud.get_project_folder(
            db=db,
            folder_id=folder_id,
        )

        from app.project_folders.validators import (
            FolderValidator,
        )

        folder = FolderValidator.validate_folder_exists(
            db=db,
            folder_id=folder_id,
        )

        crud.delete_project_folder(
            db=db,
            project_folder=folder,
        )


folder_delete_service = FolderDeleteService()
