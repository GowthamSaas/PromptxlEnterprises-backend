from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProjectFileResponse(BaseModel):
    id: int
    project_id: int
    file_name: str
    file_path: str
    language: Optional[str]
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class FileContentResponse(BaseModel):
    id: int
    file_name: str
    file_path: str
    language: Optional[str]
    content: str

    class Config:
        from_attributes = True


class UpdateFileRequest(BaseModel):
    content: str = Field(...)


class RenameFileRequest(BaseModel):
    file_name: str = Field(
        ...,
        min_length=1,
    )


class CreateFileRequest(BaseModel):
    project_id: int
    file_name: str
    file_path: str
    language: Optional[str] = None
    content: str = ""


class ExplorerNodeResponse(BaseModel):
    id: Optional[int] = None
    name: str
    path: str
    type: str
    language: Optional[str] = None
    children: list["ExplorerNodeResponse"] = Field(
        default_factory=list
    )

    class Config:
        from_attributes = True


ExplorerNodeResponse.model_rebuild()