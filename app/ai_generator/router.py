from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.ai_generator.schemas import GenerateAppRequest, GenerateAppResponse
from app.ai_generator.service import AIGenerationService
from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.user import User

router = APIRouter()
service = AIGenerationService()


@router.post("/generate", response_model=GenerateAppResponse, status_code=status.HTTP_200_OK)
def generate_app_endpoint(
    payload: GenerateAppRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GenerateAppResponse:
    try:
        result = service.generate_app(
            prompt=payload.prompt,
            app_name=payload.app_name,
            template=payload.template,
            provider=payload.provider,
            stream=payload.stream,
        )
    except Exception as exc:  # pragma: no cover - defensive wrapper
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(exc)) from exc

    return GenerateAppResponse(**result)
