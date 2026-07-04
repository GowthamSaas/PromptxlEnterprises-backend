from sqlalchemy.orm import Session

from app.projects import crud
from app.projects.models import Project
from app.projects.schemas import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
)


class ProjectService:

    @staticmethod
    def create_project(
        db: Session,
        user_id: int,
        request: ProjectCreateRequest,
    ) -> Project:

        return crud.create_project(
            db=db,
            user_id=user_id,
            name=request.name,
            description=request.description,
            provider=request.provider,
            model=request.model,
            status="generated",
        )

    @staticmethod
    def get_project(
        db: Session,
        project_id: int,
    ):

        project = crud.get_project(
            db=db,
            project_id=project_id,
        )

        if project is None:
            raise ValueError("Project not found.")

        return project

    @staticmethod
    def get_projects(
        db: Session,
        user_id: int,
    ):

        return crud.get_user_projects(
            db=db,
            user_id=user_id,
        )

    @staticmethod
    def update_project(
        db: Session,
        project_id: int,
        request: ProjectUpdateRequest,
    ):

        project = crud.get_project(
            db=db,
            project_id=project_id,
        )

        if project is None:
            raise ValueError("Project not found.")

        update_data = request.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        return crud.update_project(
            db=db,
            project=project,
            **update_data,
        )

    @staticmethod
    def delete_project(
        db: Session,
        project_id: int,
    ):

        project = crud.get_project(
            db=db,
            project_id=project_id,
        )

        if project is None:
            raise ValueError("Project not found.")

        crud.delete_project(
            db=db,
            project=project,
        )

        return {"message": "Project deleted successfully."}


project_service = ProjectService()