from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class CreateFolderRequest(BaseModel):
    project_id: int
    folder_name: str
    folder_path: str
    parent_folder_id: Optional[int] = None


class RenameFolderRequest(BaseModel):
    folder_name: str


class ProjectFolderResponse(BaseModel):
    id: int
    project_id: int
    folder_name: str
    folder_path: str
    parent_folder_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True