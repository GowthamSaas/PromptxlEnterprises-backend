from sqlalchemy.orm import Session

from app.projects.models import ProjectFolder


# -------------------------
# Project Folder CRUD
# -------------------------


def create_project_folder(
    db: Session,
    **kwargs,
) -> ProjectFolder:

    project_folder = ProjectFolder(**kwargs)

    db.add(project_folder)
    db.commit()
    db.refresh(project_folder)

    return project_folder


def get_project_folder(
    db: Session,
    folder_id: int,
) -> ProjectFolder | None:

    return (
        db.query(ProjectFolder)
        .filter(ProjectFolder.id == folder_id)
        .first()
    )


def get_project_folders(
    db: Session,
    project_id: int,
):    
    
    return (
        db.query(ProjectFolder)
        .filter(ProjectFolder.project_id == project_id)
        .order_by(ProjectFolder.folder_path.asc())
        .all()
    )

def delete_project_folder(
    db: Session,
    project_folder: ProjectFolder,
):

    db.delete(project_folder)
    db.commit()
    
def update_project_folder(
    db: Session,
    project_folder: ProjectFolder,
    **kwargs,
):
    for key, value in kwargs.items():
        setattr(project_folder, key, value)

    db.commit()
    db.refresh(project_folder)

    return project_folder