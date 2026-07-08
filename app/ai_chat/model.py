from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    DateTime,
    ForeignKey,
)

from sqlalchemy.orm import relationship

from app.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    project_id = Column(
        Integer,
        ForeignKey("projects.id"),
        nullable=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
    )

    title = Column(
        String,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    session_id = Column(
        Integer,
        ForeignKey("chat_sessions.id"),
        nullable=False,
    )

    role = Column(
        String,
        nullable=False,
    )

    message = Column(
        Text,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    session = relationship(
        "ChatSession",
        back_populates="messages",
    )