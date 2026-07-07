from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from sqlalchemy.orm import Session
from app.projects.schemas import ProjectResponse

from app.database import get_db
from app.auth.dependencies import get_current_user

from app.project_assignments.schemas import (
    AssignProjectRequest,
    ProjectAssignmentResponse,
)

from app.project_assignments.service import (
    project_assignment_service,
)

router = APIRouter()


@router.post(
    "",
    response_model=ProjectAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
def assign_project(
    request: AssignProjectRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:

        return project_assignment_service.assign_project(
            db=db,
            user_id=request.user_id,
            project_id=request.project_id,
            assigned_by=current_user.id,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )


@router.get(
    "/project/{project_id}",
    response_model=list[ProjectAssignmentResponse],
)
def get_project_assignments(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return project_assignment_service.get_project_assignments(
        db=db,
        project_id=project_id,
    )


@router.get(
    "/user/{user_id}",
    response_model=list[ProjectAssignmentResponse],
)
def get_user_assignments(
    user_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return project_assignment_service.get_user_assignments(
        db=db,
        user_id=user_id,
    )


@router.delete(
    "/{user_id}/{project_id}",
)
def remove_assignment(
    user_id: int,
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:

        return project_assignment_service.remove_assignment(
            db=db,
            user_id=user_id,
            project_id=project_id,
        )

    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        )

@router.get(
    "/my-projects",
    response_model=list[ProjectResponse],
)
def get_my_projects(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return project_assignment_service.get_my_projects(
        db=db,
        user_id=current_user.id,
    )