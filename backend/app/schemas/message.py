"""Pydantic schemas for Message resources."""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.models.message import MessageRole
from app.schemas.artifact import ArtifactRead
from app.schemas.base import ORMBase


class MessageCreate(BaseModel):
    """Payload for POST /api/v1/chat/{session_id}/message.

    Only the human-authored content is accepted from clients; `role`
    defaults to "user" since that's the only role a client should be
    able to post as. Assistant/system messages are created internally
    by the service layer (e.g. by future agent/LLM integrations).
    """

    content: str = Field(..., min_length=1, description="The message text.")
    role: MessageRole = Field(
        default=MessageRole.USER,
        description="Author of the message. Clients should always send 'user'.",
    )


class MessageRead(ORMBase):
    """Message representation returned to API clients."""

    id: uuid.UUID
    chat_session_id: uuid.UUID
    role: MessageRole
    content: str
    created_at: datetime
    updated_at: datetime
    artifact: Optional[ArtifactRead] = None
