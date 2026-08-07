from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.project_folders.schemas import (
    CreateFolderRequest,
    MoveFolderRequest,
    ProjectFolderResponse,
    RenameFolderRequest,
)
from app.project_folders.service import project_folder_service


router = APIRouter()


@router.get("/project/{project_id}", response_model=list[ProjectFolderResponse])
def get_project_folders(project_id: int, db: Session = Depends(get_db), _current_user=Depends(get_current_user)):
    return project_folder_service.get_folders(db, project_id)


@router.get("/project/{project_id}/tree")
def get_project_folder_tree(project_id: int, db: Session = Depends(get_db), _current_user=Depends(get_current_user)):
    return project_folder_service.get_tree(db, project_id)


@router.post("", response_model=ProjectFolderResponse)
def create_project_folder(request: CreateFolderRequest, db: Session = Depends(get_db), _current_user=Depends(get_current_user)):
    try:
        return project_folder_service.create_folder(db, request.project_id, request.folder_name, request.folder_path)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/project/{project_id}/move")
def move_project_folder(project_id: int, request: MoveFolderRequest, db: Session = Depends(get_db), _current_user=Depends(get_current_user)):
    try:
        path = project_folder_service.move_folder(db, project_id, request.source_path, request.destination_path)
        return {"folder_path": path}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.put("/{folder_id}", response_model=ProjectFolderResponse)
def rename_project_folder(folder_id: int, request: RenameFolderRequest, db: Session = Depends(get_db), _current_user=Depends(get_current_user)):
    try:
        return project_folder_service.rename_folder(db, folder_id, request.folder_name)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.delete("/{folder_id}")
def delete_project_folder(folder_id: int, db: Session = Depends(get_db), _current_user=Depends(get_current_user)):
    try:
        project_folder_service.delete_folder(db, folder_id)
        return {"message": "Project folder deleted successfully."}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))