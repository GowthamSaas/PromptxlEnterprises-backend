from sqlalchemy.orm import Session

from app.projects.models import ProjectFile


# -------------------------
# Project File CRUD
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


def get_project_file(
    db: Session,
    file_id: int,
) -> ProjectFile | None:

    return (
        db.query(ProjectFile)
        .filter(ProjectFile.id == file_id)
        .first()
    )


def get_project_files(
    db: Session,
    project_id: int,
):

    return (
        db.query(ProjectFile)
        .filter(ProjectFile.project_id == project_id)
        .order_by(ProjectFile.file_path.asc())
        .all()
    )


def update_project_file(
    db: Session,
    project_file: ProjectFile,
    **kwargs,
) -> ProjectFile:

    for key, value in kwargs.items():
        setattr(project_file, key, value)

    db.commit()
    db.refresh(project_file)

    return project_file


def delete_project_file(
    db: Session,
    project_file: ProjectFile,
):

    db.delete(project_file)
    db.commit()


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