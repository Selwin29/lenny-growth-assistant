"""
Domain models package.

All SQLAlchemy model classes must be imported here so that:
1. `app.database.session.Base.metadata` is aware of every table
   (required for Alembic autogenerate and `Base.metadata.create_all`).
2. String-based relationship references (e.g. "ChatSession") resolve
   correctly regardless of import order elsewhere in the app.
"""

from app.models.artifact import Artifact, ArtifactType
from app.models.chat_session import ChatSession
from app.models.message import Message, MessageRole
from app.models.user import User

__all__ = [
    "User",
    "ChatSession",
    "Message",
    "MessageRole",
    "Artifact",
    "ArtifactType",
]
