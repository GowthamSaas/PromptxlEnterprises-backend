from typing import List

from pydantic import BaseModel


class ModifyRequest(BaseModel):

    project_id: int

    prompt: str

    provider: str

    model: str


class ModifiedFile(BaseModel):

    path: str

    language: str

    content: str


class ModifyResponse(BaseModel):

    success: bool

    message: str

    modified_files: List[ModifiedFile]