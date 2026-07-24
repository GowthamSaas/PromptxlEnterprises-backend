from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import traceback

from app.database import get_db
from app.auth.dependencies import get_current_user

from app.project_folders.schemas import (
    ProjectFolderResponse,
    CreateFolderRequest,
    RenameFolderRequest,
)

from app.project_folders.service import (
    project_folder_service,
)

router = APIRouter()


@router.get(
    "/project/{project_id}",
    response_model=list[ProjectFolderResponse],
)
def get_project_folders(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:

        return project_folder_service.get_project_folders(
            db=db,
            project_id=project_id,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )




@router.post(
    "",
    response_model=ProjectFolderResponse,
)
def create_project_folder(
    request: CreateFolderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    print("===== REQUEST =====")
    print(request.model_dump())

    try:

        folder = project_folder_service.create_project_folder(
            db=db,
            project_id=request.project_id,
            folder_name=request.folder_name,
            folder_path=request.folder_path,
            parent_folder_id=request.parent_folder_id,
        )

        print("===== CREATED =====")
        print(folder)

        return folder

    except Exception as exc:

        print("===== ERROR =====")
        traceback.print_exc()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.put(
    "/{folder_id}",
    response_model=ProjectFolderResponse,
)
def rename_project_folder(
    folder_id: int,
    request: RenameFolderRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:

        return project_folder_service.rename_project_folder(
            db=db,
            folder_id=folder_id,
            folder_name=request.folder_name,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.delete("/{folder_id}")
def delete_project_folder(
    folder_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_folder_service.delete_project_folder(
            db=db,
            folder_id=folder_id,
        )

    except Exception as exc:
        print("===== DELETE ERROR =====")
        traceback.print_exc()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )   
        
        
@router.get("/project/{project_id}/tree")
def get_project_tree(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return project_folder_service.get_project_tree(
            db=db,
            project_id=project_id,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )