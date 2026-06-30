from pydantic import BaseModel
from datetime import datetime
from typing import List

class AssignmentCreate(BaseModel):
    user_id: int
    application_ids: List[int]

class AssignmentResponse(BaseModel):
    id: int
    user_id: int
    application_id: int
    assigned_at: datetime
    assigned_by: int

    class Config:
        from_attributes = True
