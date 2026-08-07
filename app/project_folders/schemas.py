from datetime import datetime

from pydantic import BaseModel, Field


class CreateFolderRequest(BaseModel):
    project_id: int
    folder_name: str = Field(..., min_length=1)
    folder_path: str = Field(..., min_length=1)


class RenameFolderRequest(BaseModel):
    folder_name: str = Field(..., min_length=1)


class MoveFolderRequest(BaseModel):
    source_path: str = Field(..., min_length=1)
    destination_path: str = ""


class ProjectFolderResponse(BaseModel):
    id: int
    project_id: int
    folder_name: str
    folder_path: str
    created_at: datetime

    class Config:
        from_attributes = True