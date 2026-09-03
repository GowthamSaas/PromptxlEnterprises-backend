from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)

from sqlalchemy.orm import Session

from app.database import get_db

from app.auth.dependencies import (
    get_current_user,
)

from app.deployment.schemas import (
    DeploymentRequest,
    DeploymentResponse,
)

from app.deployment.service import (
    deployment_service,
)

router = APIRouter()


# =====================================================
# Deploy Project
# =====================================================

@router.post(
    "/deploy",
    response_model=DeploymentResponse,
    status_code=status.HTTP_200_OK,
)
async def deploy_project(
    request: DeploymentRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    try:

        return await deployment_service.deploy(
            db=db,
            user=current_user,
            request=request,
        )

    except HTTPException:
        # Re-raise HTTPException to preserve status code
        raise

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/{deployment_id}",
)
def get_deployment(
    deployment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return deployment_service.get_deployment(
        db=db,
        deployment_id=deployment_id,
    )



@router.get(
    "/project/{project_id}",
)
def get_project_deployments(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return deployment_service.get_project_deployments(
        db=db,
        project_id=project_id,
    )



@router.get(
    "/{deployment_id}/logs",
)
def get_logs(
    deployment_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return deployment_service.get_logs(
        db=db,
        deployment_id=deployment_id,
    )