"""Service layer for ChatSession CRUD operations.

Routes should never touch SQLAlchemy models directly — they call into
this module, which encapsulates all query/persistence logic and raises
domain exceptions (from app.core.exceptions) on failure.
"""

import logging
import uuid
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.models.chat_session import ChatSession
from app.schemas.chat_session import ChatSessionCreate, ChatSessionUpdate

logger = logging.getLogger(__name__)


def create_chat_session(db: Session, user_id: uuid.UUID, payload: ChatSessionCreate) -> ChatSession:
    """Create and persist a new ChatSession owned by the given user."""
    chat_session = ChatSession(user_id=user_id, title=payload.title)
    db.add(chat_session)
    db.commit()
    db.refresh(chat_session)
    logger.info("Created chat session id=%s user_id=%s", chat_session.id, user_id)
    return chat_session


def list_chat_sessions(db: Session, user_id: uuid.UUID) -> List[ChatSession]:
    """Return all ChatSessions for a user, most recently updated first."""
    stmt = (
        select(ChatSession)
        .where(ChatSession.user_id == user_id)
        .order_by(ChatSession.updated_at.desc())
    )
    return list(db.scalars(stmt).all())


def get_chat_session(db: Session, session_id: uuid.UUID, *, with_messages: bool = False) -> ChatSession:
    """Fetch a single ChatSession by id.

    Raises:
        NotFoundError: If no session with that id exists.
    """
    stmt = select(ChatSession).where(ChatSession.id == session_id)
    if with_messages:
        stmt = stmt.options(selectinload(ChatSession.messages))
    chat_session = db.scalars(stmt).first()
    if chat_session is None:
        raise NotFoundError(f"Chat session '{session_id}' not found")
    return chat_session


def update_chat_session(db: Session, session_id: uuid.UUID, payload: ChatSessionUpdate) -> ChatSession:
    """Apply a partial update to a ChatSession (currently: title only)."""
    chat_session = get_chat_session(db, session_id)
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chat_session, field, value)
    db.commit()
    db.refresh(chat_session)
    logger.info("Updated chat session id=%s fields=%s", session_id, list(update_data.keys()))
    return chat_session


def delete_chat_session(db: Session, session_id: uuid.UUID) -> None:
    """Delete a ChatSession (and cascade its Messages/Artifacts)."""
    chat_session = get_chat_session(db, session_id)
    db.delete(chat_session)
    db.commit()
    logger.info("Deleted chat session id=%s", session_id)
