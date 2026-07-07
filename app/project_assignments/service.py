from sqlalchemy.orm import Session

from app.models.user import User
from app.projects.models import Project

from app.project_assignments import crud


class ProjectAssignmentService:

    @staticmethod
    def assign_project(
        db: Session,
        user_id: int,
        project_id: int,
        assigned_by: int,
    ):

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if user is None:
            raise ValueError("User not found.")

        project = (
            db.query(Project)
            .filter(Project.id == project_id)
            .first()
        )

        if project is None:
            raise ValueError("Project not found.")

        assignment = crud.get_assignment(
            db=db,
            user_id=user_id,
            project_id=project_id,
        )

        if assignment:
            raise ValueError(
                "Project already assigned."
            )

        return crud.create_assignment(
            db=db,
            user_id=user_id,
            project_id=project_id,
            assigned_by=assigned_by,
        )

    @staticmethod
    def get_project_assignments(
        db: Session,
        project_id: int,
    ):
        return crud.get_project_assignments(
            db=db,
            project_id=project_id,
        )

    @staticmethod
    def get_user_assignments(
        db: Session,
        user_id: int,
    ):
        return crud.get_user_assignments(
            db=db,
            user_id=user_id,
        )

    @staticmethod
    def remove_assignment(
        db: Session,
        user_id: int,
        project_id: int,
    ):

        assignment = crud.get_assignment(
            db=db,
            user_id=user_id,
            project_id=project_id,
        )

        if assignment is None:
            raise ValueError(
                "Assignment not found."
            )

        crud.delete_assignment(
            db=db,
            assignment=assignment,
        )

        return {
            "message": "Project assignment removed successfully."
        }


    @staticmethod
    def get_my_projects(
        db: Session,
        user_id: int,
    ):
        return crud.get_my_projects(
            db=db,
            user_id=user_id,
        )


project_assignment_service = ProjectAssignmentService()