from pathlib import PurePosixPath

from sqlalchemy.orm import Session

from app.project_files import crud
from app.project_files.exceptions import (
    ProjectFileAlreadyExistsException,
    ProjectFileNotFoundException,
)


class FileMoveService:
    @staticmethod
    def move_file(
        db: Session,
        file_id: int,
        destination_path: str,
    ):
        project_file = crud.get_project_file(db=db, file_id=file_id)
        if project_file is None:
            raise ProjectFileNotFoundException("Project file not found.")

        destination = destination_path.strip().strip("/")
        if ".." in PurePosixPath(destination).parts:
            raise ValueError("Destination path must be project-relative.")

        new_path = (
            f"{destination}/{project_file.file_name}"
            if destination
            else project_file.file_name
        )
        if new_path == project_file.file_path:
            return project_file

        for file in crud.get_project_files(db=db, project_id=project_file.project_id):
            if file.id != project_file.id and file.file_path == new_path:
                raise ProjectFileAlreadyExistsException(
                    "A file with this name already exists in the destination folder."
                )

        return crud.update_project_file(
            db=db,
            project_file=project_file,
            file_path=new_path,
        )


file_move_service = FileMoveService()