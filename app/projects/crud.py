from sqlalchemy.orm import Session

from app.projects.models import Project, ProjectFile


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


# -------------------------
# Project Files CRUD
# -------------------------

def create_project_file(
    db: Session,
    **kwargs,
) -> ProjectFile:

    project_file = ProjectFile(**kwargs)

    db.add(project_file)
    db.commit()
    db.refresh(project_file)

    return project_file


def create_project_files(
    db: Session,
    files: list[ProjectFile],
):

    db.add_all(files)
    db.commit()


def get_project_files(
    db: Session,
    project_id: int,
):

    return (
        db.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .all()
    )


def delete_project_files(
    db: Session,
    project_id: int,
):

    (
        db.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .delete()
    )

    db.commit()