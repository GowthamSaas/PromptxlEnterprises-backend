from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse
from pathlib import Path


from app.database import get_db
from app.auth.dependencies import get_current_user

from app.projects.schemas import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
)

from app.projects.service import project_service


router = APIRouter()


@router.post(
    "",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_project(
    request: ProjectCreateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_service.create_project(
            db=db,
            user_id=current_user.id,
            request=request,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "",
    response_model=list[ProjectResponse],
)
def get_projects(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return project_service.get_projects(
        db=db,
        user_id=current_user.id,
    )


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_service.get_project(
            db=db,
            project_id=project_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        )


@router.put(
    "/{project_id}",
    response_model=ProjectResponse,
)
def update_project(
    project_id: int,
    request: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_service.update_project(
            db=db,
            project_id=project_id,
            request=request,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_service.delete_project(
            db=db,
            project_id=project_id,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/{project_id}/export",
)
def export_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:

        zip_path: Path = project_service.export_project(
            db=db,
            project_id=project_id,
        )

        
       

        return FileResponse(
            path=zip_path,
            filename=f"{project_service.get_project(db, project_id).name}.zip",
            media_type="application/zip",
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )