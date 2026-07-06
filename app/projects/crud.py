from sqlalchemy.orm import Session

from app.projects.models import Project


# -------------------------
# Project CRUD
# -------------------------

def create_project(
    db: Session,
    **kwargs,
) -> Project:

    project = Project(**kwargs)

    db.add(project)
    db.commit()
    db.refresh(project)

    return project


def get_project(
    db: Session,
    project_id: int,
) -> Project | None:

    return (
        db.query(Project)
        .filter(Project.id == project_id)
        .first()
    )


def get_user_projects(
    db: Session,
    user_id: int,
):

    return (
        db.query(Project)
        .filter(Project.user_id == user_id)
        .order_by(Project.created_at.desc())
        .all()
    )


def update_project(
    db: Session,
    project: Project,
    **kwargs,
) -> Project:

    for key, value in kwargs.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)

    return project


def delete_project(
    db: Session,
    project: Project,
):

    db.delete(project)
    db.commit()