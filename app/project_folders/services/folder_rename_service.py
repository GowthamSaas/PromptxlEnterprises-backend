from sqlalchemy.orm import Session

from app.project_folders import crud


class FolderRenameService:

    @staticmethod
    def rename_folder(
        db: Session,
        folder_id: int,
        folder_name: str,
    ):

        from app.project_folders.validators import (
        FolderValidator,
        )

        folder = FolderValidator.validate_folder_exists(
            db=db,
            folder_id=folder_id,
        )

        folder_path = folder.folder_path.split("/")

        folder_path[-1] = folder_name

        new_path = "/".join(folder_path)

        return crud.update_project_folder(
            db=db,
            project_folder=folder,
            folder_name=folder_name,
            folder_path=new_path,
        )


folder_rename_service = FolderRenameService()