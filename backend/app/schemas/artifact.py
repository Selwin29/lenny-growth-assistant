"""Pydantic schemas for Artifact resources."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.artifact import ArtifactType
from app.schemas.base import ORMBase


class ArtifactCreate(BaseModel):
    """Payload for creating an Artifact (used internally by the service layer)."""

    title: str = Field(..., min_length=1, max_length=255)
    artifact_type: ArtifactType = ArtifactType.TEXT
    content: str = Field(..., min_length=1)


class ArtifactRead(ORMBase):
    """Artifact representation returned to API clients."""

    id: uuid.UUID
    message_id: uuid.UUID
    title: str
    artifact_type: ArtifactType
    content: str
    created_at: datetime
    updated_at: datetime
