from sqlalchemy.orm import Session
from app.project_folders import crud

from app.project_folders.services.folder_create_service import folder_create_service
from app.project_folders.services.folder_delete_service import folder_delete_service
from app.project_folders.services.folder_rename_service import folder_rename_service
from app.project_folders.services.explorer_service import folder_explorer_service


class ProjectFolderService:

    def get_project_folders(
        self,
        db: Session,
        project_id: int,
    ):
        return crud.get_project_folders(
            db=db,
            project_id=project_id,
        )

    def create_project_folder(
        self,
        db: Session,
        project_id: int,
        folder_name: str,
        folder_path: str,
        parent_folder_id: int | None = None,
    ):
        return folder_create_service.create_folder(
            db=db,
            project_id=project_id,
            folder_name=folder_name,
            folder_path=folder_path,
            parent_folder_id=parent_folder_id,
        )

    def rename_project_folder(
        self,
        db: Session,
        folder_id: int,
        folder_name: str,
    ):
        return folder_rename_service.rename_folder(
            db=db,
            folder_id=folder_id,
            folder_name=folder_name,
        )

    def delete_project_folder(
        self,
        db: Session,
        folder_id: int,
    ):
        return folder_delete_service.delete_folder(
            db=db,
            folder_id=folder_id,
        )

    def get_project_tree(
        self,
        db: Session,
        project_id: int,
    ):
        return folder_explorer_service.build_tree(
            db=db,
            project_id=project_id,
        )


project_folder_service = ProjectFolderService()