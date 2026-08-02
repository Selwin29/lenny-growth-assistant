"""User model.

Minimal user record for now — no authentication/password handling yet
(that arrives in a later milestone). Exists primarily so ChatSessions
have an owner.
"""

from typing import List

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A user of the Lenny Growth Assistant.

    Relationships:
        chat_sessions: All ChatSessions owned by this user (one-to-many).
    """

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    chat_sessions: Mapped[List["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<User id={self.id} email={self.email!r}>"
