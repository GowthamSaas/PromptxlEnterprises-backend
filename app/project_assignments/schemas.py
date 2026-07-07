from datetime import datetime
from pydantic import BaseModel, Field


class AssignProjectRequest(BaseModel):
    user_id: int = Field(..., gt=0)
    project_id: int = Field(..., gt=0)


class ProjectAssignmentResponse(BaseModel):
    id: int
    user_id: int
    project_id: int
    assigned_by: int
    assigned_at: datetime

    class Config:
        from_attributes = True


class AssignedUserResponse(BaseModel):
    user_id: int
    project_id: int