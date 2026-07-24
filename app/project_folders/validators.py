from app.project_folders import crud

from app.project_folders.exceptions import (
    ProjectFolderAlreadyExistsException,
    ProjectFolderNotFoundException,
)


class FolderValidator:

    @staticmethod
    def validate_folder_exists(
        db,
        folder_id: int,
    ):

        folder = crud.get_project_folder(
            db=db,
            folder_id=folder_id,
        )

        if not folder:

            raise ProjectFolderNotFoundException(
                "Folder not found."
            )

        return folder

    @staticmethod
    def validate_duplicate_folder(
        db,
        project_id: int,
        folder_path: str,
    ):

        folders = crud.get_project_folders(
            db=db,
            project_id=project_id,
        )

        for folder in folders:

            if folder.folder_path == folder_path:

                raise ProjectFolderAlreadyExistsException(
                    "Folder already exists."
                )