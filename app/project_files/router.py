from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db

from app.project_files.schemas import (
    ProjectFileResponse,
    UpdateFileRequest,
    CreateFileRequest,
    RenameFileRequest,
)

from app.project_files.service import (
    project_file_service,
)

router = APIRouter()


@router.get(
    "/project/{project_id}",
    response_model=list[ProjectFileResponse],
)
def get_project_files(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_file_service.get_project_files(
            db=db,
            project_id=project_id,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/{file_id}",
    response_model=ProjectFileResponse,
)
def get_project_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_file_service.get_project_file(
            db=db,
            file_id=file_id,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )

@router.get(
    "/project/{project_id}/tree",
)
def get_project_tree(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_file_service.get_project_tree(
            db=db,
            project_id=project_id,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.put(
    "/{file_id}",
    response_model=ProjectFileResponse,
)
def update_project_file(
    file_id: int,
    request: UpdateFileRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_file_service.update_project_file(
            db=db,
            file_id=file_id,
            content=request.content,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.delete(
    "/{file_id}",
)
def delete_project_file(
    file_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_file_service.delete_project_file(
            db=db,
            file_id=file_id,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.post(
    "",
    response_model=ProjectFileResponse,
)
def create_project_file(
    request: CreateFileRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_file_service.create_project_file(
            db=db,
            project_id=request.project_id,
            file_name=request.file_name,
            file_path=request.file_path,
            language=request.language,
            content=request.content,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.put(
    "/{file_id}/rename",
    response_model=ProjectFileResponse,
)
def rename_project_file(
    file_id: int,
    request: RenameFileRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_file_service.rename_project_file(
            db=db,
            file_id=file_id,
            new_file_name=request.file_name,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )