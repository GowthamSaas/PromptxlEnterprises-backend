from sqlalchemy.orm import Session

from app.projects.models import Project
from app.ai_chat.model import ChatSession, ChatMessage


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
    session_ids = db.query(ChatSession.id).filter(
        ChatSession.project_id == project.id
    ).subquery()

    db.query(ChatMessage).filter(
        ChatMessage.session_id.in_(session_ids)
    ).delete(synchronize_session=False)

    db.query(ChatSession).filter(
        ChatSession.project_id == project.id
    ).delete(synchronize_session=False)

    db.delete(project)
    db.commit()