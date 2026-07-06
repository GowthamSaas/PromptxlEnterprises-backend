from sqlalchemy.orm import Session

from app.projects.models import Project

from app.project_files.services.explorer_service import (
    explorer_service,
)
from app.project_files.services.file_content_service import (
    file_content_service,
)
from app.project_files.services.file_save_service import (
    file_save_service,
)
from app.project_files.services.file_create_service import (
    file_create_service,
)
from app.project_files.services.file_delete_service import (
    file_delete_service,
)
from app.project_files.services.file_rename_service import (
    file_rename_service,
)
from app.project_files.validators import (
    ProjectFileValidator,
)
from app.project_files import crud


class ProjectFileService:

    @staticmethod
    def save_project_files(
        db: Session,
        project: Project,
        files: list[dict],
    ):
        """
        Save AI generated project files.
        """

        ProjectFileValidator.validate_files(files)

        for file in files:

            crud.create_project_file(
                db=db,
                project_id=project.id,
                file_name=file["path"].split("/")[-1],
                file_path=file["path"],
                language=file.get("language"),
                content=file["content"],
            )

    @staticmethod
    def get_project_files(
       db: Session,
       project_id: int,
    ):
        return crud.get_project_files(
           db=db,
           project_id=project_id,
        )

    @staticmethod
    def get_project_file(
        db: Session,
        file_id: int,
    ):
        return file_content_service.get_file_content(
            db=db,
            file_id=file_id,
        )

    
    @staticmethod
    def get_project_tree(
        db: Session,
        project_id: int,
    ):
        return explorer_service.build_tree(
            db=db,
            project_id=project_id,
        )

    @staticmethod
    def update_project_file(
        db: Session,
        file_id: int,
        content: str,
    ):
        return file_save_service.save_file(
            db=db,
            file_id=file_id,
            content=content,
        )

    @staticmethod
    def create_project_file(
        db: Session,
        project_id: int,
        file_name: str,
        file_path: str,
        language: str | None = None,
        content: str = "",
    ):
        return file_create_service.create_file(
            db=db,
            project_id=project_id,
            file_name=file_name,
            file_path=file_path,
            language=language,
            content=content,
        )

    @staticmethod
    def rename_project_file(
        db: Session,
        file_id: int,
        new_file_name: str,
    ):
        return file_rename_service.rename_file(
            db=db,
            file_id=file_id,
            new_file_name=new_file_name,
        )

    @staticmethod
    def delete_project_file(
        db: Session,
        file_id: int,
    ):
        return file_delete_service.delete_file(
            db=db,
            file_id=file_id,
        )


project_file_service = ProjectFileService()