"""Artifact model.

Represents generated content attached to an assistant Message (e.g. a
document, code snippet, or chart). Actual artifact generation logic
arrives in a later milestone — this milestone only defines the storage
shape.
"""

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class ArtifactType(str, enum.Enum):
    """The kind of content an Artifact holds."""

    TEXT = "text"
    CODE = "code"
    MARKDOWN = "markdown"
    JSON = "json"
    CHART = "chart"


class Artifact(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A generated artifact attached to exactly one Message.

    Relationships:
        message: The owning Message (one-to-one).
    """

    __tablename__ = "artifacts"

    message_id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("messages.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    artifact_type: Mapped[ArtifactType] = mapped_column(
        Enum(ArtifactType, name="artifact_type", values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ArtifactType.TEXT,
    )

    content: Mapped[str] = mapped_column(Text, nullable=False)

    message: Mapped["Message"] = relationship("Message", back_populates="artifact")

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"<Artifact id={self.id} type={self.artifact_type.value}>"
