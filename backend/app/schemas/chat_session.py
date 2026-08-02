"""Pydantic schemas for ChatSession resources."""

import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.base import ORMBase
from app.schemas.message import MessageRead


class ChatSessionCreate(BaseModel):
    """Payload for POST /api/v1/chat/new."""

    title: str = Field(default="New Chat", min_length=1, max_length=255)


class ChatSessionUpdate(BaseModel):
    """Payload for PATCH /api/v1/chat/{session_id}.

    All fields optional — only supplied fields are updated.
    """

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)


class ChatSessionRead(ORMBase):
    """Summary representation of a ChatSession (used in list views)."""

    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime


class ChatSessionDetail(ChatSessionRead):
    """Full representation of a ChatSession including its messages."""

    messages: List[MessageRead] = []
