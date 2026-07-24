from sqlalchemy.orm import Session

from app.project_folders import crud


class FolderCreateService:

    @staticmethod
    def create_folder(
        db: Session,
        project_id: int,
        folder_name: str,
        folder_path: str,
        parent_folder_id: int | None = None,
    ):

        from app.project_folders.validators import (
        FolderValidator,
        )
        print("Received folder_path:", folder_path)
        print("Received project_id:", project_id)
        
        FolderValidator.validate_duplicate_folder(
            db=db,
            project_id=project_id,
            folder_path=folder_path,
        )

        return crud.create_project_folder(
            db=db,
            project_id=project_id,
            folder_name=folder_name,
            folder_path=folder_path,
            parent_folder_id=parent_folder_id,
        )


folder_create_service = FolderCreateService()