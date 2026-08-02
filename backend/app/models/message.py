"""Message model.

A single message within a ChatSession, authored by either the user or
the assistant. May optionally have one associated Artifact (e.g. a
generated document, code snippet, chart, etc. — populated by a later
milestone).
"""

import enum
import uuid
from typing import Optional

from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class MessageRole(str, enum.Enum):
    """Author of a message."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class Message(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A single message within a ChatSession.

    Relationships:
        chat_session: The parent ChatSession (many-to-one).
        artifact: An optional single Artifact attached to this message
            (one-to-one).
    """

    __tablename__ = "messages"

    chat_session_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    chat_session: Mapped["ChatSession"] = relationship("ChatSession", back_populates="messages")
    artifact: Mapped[Optional["Artifact"]] = relationship(
        "Artifact",
        back_populates="message",
        uselist=False,
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Message id={self.id} role={self.role.value}>"
