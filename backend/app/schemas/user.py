"""Pydantic schemas for User resources.

Minimal for now — no authentication/password fields. A later milestone
will extend this with credentials, tokens, etc.
"""

import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr, Field

from app.schemas.base import ORMBase


class UserCreate(BaseModel):
    """Payload for creating a User."""

    email: EmailStr
    full_name: Optional[str] = Field(default=None, max_length=255)


class UserRead(ORMBase):
    """User representation returned to API clients."""

    id: uuid.UUID
    email: str
    full_name: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
