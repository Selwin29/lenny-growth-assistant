"""
Shared SQLAlchemy model mixins.

Every domain model in this app uses a UUID primary key and
created_at/updated_at timestamps, so that boilerplate lives here once
and gets inherited rather than duplicated across model files.
"""

import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column


def _utcnow() -> datetime:
    """Return the current UTC time (used as a default for timestamp columns)."""
    return datetime.now(timezone.utc)


class UUIDPrimaryKeyMixin:
    """Adds a UUID primary key column named `id`.

    Uses PostgreSQL's native UUID type. The ORM generates the UUID
    client-side via `uuid.uuid4`, so IDs are available immediately
    after object construction (before a flush/commit).
    """

    id: Mapped[uuid.UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )


class TimestampMixin:
    """Adds `created_at` and `updated_at` timestamp columns.

    Both are timezone-aware and stored in UTC. `updated_at` is
    automatically refreshed on every UPDATE via `onupdate`.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=_utcnow,
        onupdate=_utcnow,
        nullable=False,
    )
