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

from app.ai_chat.schemas import (
    ChatRequest,
    ChatResponse,
)

from app.ai_chat.service import (
    ai_chat_service,
)


from typing import List

from app.ai_chat.schemas import (
    ChatHistoryResponse,
    ChatSessionResponse,
)

router = APIRouter()


@router.post(
    "/send",
    response_model=ChatResponse,
    status_code=status.HTTP_200_OK,
)
async def send_message(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Send a message to AI.
    """

    try:

        return await ai_chat_service.chat(
            db=db,
            user=current_user,
            request=request,
        )

    except Exception as exc:

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        )


@router.get(
    "/history/{session_id}",
    response_model=List[ChatHistoryResponse],
)
async def get_chat_history(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return ai_chat_service.get_chat_history(
        db=db,
        session_id=session_id,
    )



@router.get(
    "/sessions",
    response_model=List[ChatSessionResponse],
)
async def get_chat_sessions(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    return ai_chat_service.get_chat_sessions(
        db=db,
        user=current_user,
    )



@router.delete(
    "/{session_id}",
)
async def delete_chat_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):

    success = ai_chat_service.delete_chat_session(
        db=db,
        session_id=session_id,
    )

    return {
        "success": success,
    }