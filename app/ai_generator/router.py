from fastapi import APIRouter, Depends, HTTPException, status

from app.auth.dependencies import get_current_user
from app.ai_generator.schemas import (
    GenerateRequest,
    GenerateResponse
)
from app.ai_generator.service import ai_generator_service

router = APIRouter()


@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_200_OK
)
async def generate_application(
    request: GenerateRequest,
    current_user=Depends(get_current_user)
):
    """
    Generate AI response using the selected provider.
    """

    try:
        return await ai_generator_service.generate(
            user=current_user,
            request=request
        )

    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc)
        )