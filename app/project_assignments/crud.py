from sqlalchemy.orm import Session

from app.project_assignments.models import (
    ProjectAssignment,
)
from app.projects.models import Project


def create_assignment(
    db: Session,
    user_id: int,
    project_id: int,
    assigned_by: int,
):
    assignment = ProjectAssignment(
        user_id=user_id,
        project_id=project_id,
        assigned_by=assigned_by,
    )

    db.add(assignment)
    db.commit()
    db.refresh(assignment)

    return assignment


def get_assignment(
    db: Session,
    user_id: int,
    project_id: int,
):
    return (
        db.query(ProjectAssignment)
        .filter(
            ProjectAssignment.user_id == user_id,
            ProjectAssignment.project_id == project_id,
        )
        .first()
    )


def get_project_assignments(
    db: Session,
    project_id: int,
):
    return (
        db.query(ProjectAssignment)
        .filter(
            ProjectAssignment.project_id == project_id,
        )
        .all()
    )


def get_user_assignments(
    db: Session,
    user_id: int,
):
    return (
        db.query(ProjectAssignment)
        .filter(
            ProjectAssignment.user_id == user_id,
        )
        .all()
    )


def delete_assignment(
    db: Session,
    assignment: ProjectAssignment,
):
    db.delete(assignment)
    db.commit()



def get_my_projects(
    db: Session,
    user_id: int,
):
    return (
        db.query(Project)
        .join(
            ProjectAssignment,
            Project.id == ProjectAssignment.project_id,
        )
        .filter(
            ProjectAssignment.user_id == user_id,
        )
        .all()
    )