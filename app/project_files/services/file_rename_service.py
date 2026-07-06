from pathlib import PurePath

from sqlalchemy.orm import Session

from app.project_files import crud
from app.project_files.exceptions import (
    ProjectFileAlreadyExistsException,
    ProjectFileNotFoundException,
)


class FileRenameService:
    """
    Responsible for renaming a project file.
    """

    @staticmethod
    def rename_file(
        db: Session,
        file_id: int,
        new_file_name: str,
    ):

        project_file = crud.get_project_file(
            db=db,
            file_id=file_id,
        )

        if project_file is None:
            raise ProjectFileNotFoundException(
                "Project file not found."
            )

        # Duplicate file name check
        project_files = crud.get_project_files(
            db=db,
            project_id=project_file.project_id,
        )

        parent = str(
            PurePath(project_file.file_path).parent
        )

        if parent == ".":
            new_path = new_file_name
        else:
            new_path = f"{parent}/{new_file_name}"

        for file in project_files:

            if (
                file.id != project_file.id
                and file.file_path == new_path
            ):
                raise ProjectFileAlreadyExistsException(
                    "File already exists."
                )

        return crud.update_project_file(
            db=db,
            project_file=project_file,
            file_name=new_file_name,
            file_path=new_path,
        )


file_rename_service = FileRenameService()