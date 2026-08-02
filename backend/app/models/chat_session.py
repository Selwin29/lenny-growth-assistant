"""ChatSession model.

Represents a single conversation thread between a user and the
assistant. Holds many Messages.
"""

import uuid
from typing import List

from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ChatSession(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A chat conversation thread owned by a User.

    Relationships:
        user: The owning User (many-to-one).
        messages: All Messages in this session, ordered by creation time
            (one-to-many).
    """

    __tablename__ = "chat_sessions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False, default="New Chat")

    user: Mapped["User"] = relationship("User", back_populates="chat_sessions")
    messages: Mapped[List["Message"]] = relationship(
        "Message",
        back_populates="chat_session",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="Message.created_at",
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<ChatSession id={self.id} title={self.title!r}>"
