from sqlalchemy.orm import Session

from app.ai_chat.model import (
    ChatSession,
    ChatMessage,
)


class ConversationService:
    """
    Handles chat session and
    message database operations.
    """

    def create_session(
        self,
        db: Session,
        user_id: int,
        project_id: int | None = None,
        title: str | None = None,
    ) -> ChatSession:

        session = ChatSession(
            user_id=user_id,
            project_id=project_id,
            title=title,
        )

        db.add(session)
        db.commit()
        db.refresh(session)

        return session

    def get_session(
        self,
        db: Session,
        session_id: int,
    ) -> ChatSession | None:

        return (
            db.query(ChatSession)
            .filter(ChatSession.id == session_id)
            .first()
        )

    def save_message(
        self,
        db: Session,
        session_id: int,
        role: str,
        message: str,
    ) -> ChatMessage:

        chat_message = ChatMessage(
            session_id=session_id,
            role=role,
            message=message,
        )

        db.add(chat_message)
        db.commit()
        db.refresh(chat_message)

        return chat_message

    def get_messages(
        self,
        db: Session,
        session_id: int,
    ) -> list[ChatMessage]:

        return (
            db.query(ChatMessage)
            .filter(
                ChatMessage.session_id == session_id
            )
            .order_by(ChatMessage.created_at.asc())
            .all()
        )


    def get_session_messages(
        self,
        db: Session,
        session_id: int,
    ) -> list[ChatMessage]:

        return self.get_messages(
            db=db,
            session_id=session_id,
        )


    def get_user_sessions(
        self,
        db: Session,
        user_id: int,
    ) -> list[ChatSession]:

        return (
            db.query(ChatSession)
            .filter(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .all()
        )

    def delete_session(
        self,
        db: Session,
        session_id: int,
    ) -> bool:

        session = self.get_session(
           db=db,
           session_id=session_id,
        )

        if not session:
            return False

        db.delete(session)
        db.commit()

        return True


conversation_service = ConversationService()