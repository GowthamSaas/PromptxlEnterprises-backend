from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.sql import func

from app.database import Base


class ProjectFolder(Base):
    __tablename__ = "project_folders"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(
        Integer,
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
    )
    folder_name = Column(String(255), nullable=False)
    folder_path = Column(String(500), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    __table_args__ = (
        UniqueConstraint("project_id", "folder_path", name="uq_project_folder_path"),
    )