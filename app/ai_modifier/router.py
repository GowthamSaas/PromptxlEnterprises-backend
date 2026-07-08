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

from app.ai_modifier.schemas import (
    ModifyRequest,
    ModifyResponse,
)

from app.ai_modifier.service import (
    ai_modifier_service,
)

router = APIRouter()


@router.post(
    "/modify",
    response_model=ModifyResponse,
    status_code=status.HTTP_200_OK,
)
async def modify_project(
    request: ModifyRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Modify an existing project using AI.
    """

    try:

        return await ai_modifier_service.modify(
            db=db,
            user=current_user,
            request=request,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )