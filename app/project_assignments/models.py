from sqlalchemy import (
    Column,
    Integer,
    ForeignKey,
    DateTime,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database import Base



class ProjectAssignment(Base):
    __tablename__ = "project_assignments"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )

    assigned_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )

    assigned_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    # User who received the project
    user = relationship(
        "User",
        foreign_keys=[user_id],
        back_populates="assigned_projects",
    )

    # Assigned project
    project = relationship(
        "Project",
        back_populates="assigned_users",
    )

    # Owner/Admin who assigned the project
    assigned_user = relationship(
        "User",
        foreign_keys=[assigned_by],
    )