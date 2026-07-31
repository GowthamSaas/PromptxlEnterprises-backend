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

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )