"""Service layer for Message CRUD operations."""

import logging
import uuid
from datetime import datetime, timezone
from typing import List

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.exceptions import NotFoundError
from app.models.message import Message
from app.schemas.message import MessageCreate
from app.services.chat_session_service import get_chat_session

logger = logging.getLogger(__name__)


def create_message(db: Session, session_id: uuid.UUID, payload: MessageCreate) -> Message:
    """Create and persist a new Message within a ChatSession.

    Also bumps the parent ChatSession's `updated_at` so session lists
    can be sorted by most recent activity.

    Raises:
        NotFoundError: If the parent chat session does not exist.
    """
    chat_session = get_chat_session(db, session_id)

    message = Message(chat_session_id=chat_session.id, role=payload.role, content=payload.content)
    db.add(message)

    chat_session.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(message)
    logger.info(
        "Created message id=%s session_id=%s role=%s", message.id, session_id, payload.role.value
    )
    return message


def list_messages(db: Session, session_id: uuid.UUID) -> List[Message]:
    """Return all Messages in a ChatSession, oldest first.

    Raises:
        NotFoundError: If the chat session does not exist.
    """
    get_chat_session(db, session_id)  # ensures 404 if session is missing
    stmt = (
        select(Message)
        .where(Message.chat_session_id == session_id)
        .options(selectinload(Message.artifact))
        .order_by(Message.created_at)
    )
    return list(db.scalars(stmt).all())


def get_message(db: Session, message_id: uuid.UUID) -> Message:
    """Fetch a single Message by id.

    Raises:
        NotFoundError: If no message with that id exists.
    """
    message = db.get(Message, message_id)
    if message is None:
        raise NotFoundError(f"Message '{message_id}' not found")
    return message
