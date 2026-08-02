"""Service layer for Artifact CRUD operations.

Not yet exposed via any route (artifact generation is implemented in a
later milestone), but provided now so the storage layer is complete and
ready to be wired up to agent output without further schema changes.
"""

import logging
import uuid

from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.artifact import Artifact
from app.services.message_service import get_message
from app.schemas.artifact import ArtifactCreate

logger = logging.getLogger(__name__)


def create_artifact(db: Session, message_id: uuid.UUID, payload: ArtifactCreate) -> Artifact:
    """Create and persist a new Artifact attached to a Message.

    Raises:
        NotFoundError: If the parent message does not exist.
    """
    message = get_message(db, message_id)

    artifact = Artifact(
        message_id=message.id,
        title=payload.title,
        artifact_type=payload.artifact_type,
        content=payload.content,
    )
    db.add(artifact)
    db.commit()
    db.refresh(artifact)
    logger.info("Created artifact id=%s message_id=%s", artifact.id, message_id)
    return artifact


def get_artifact(db: Session, artifact_id: uuid.UUID) -> Artifact:
    """Fetch a single Artifact by id.

    Raises:
        NotFoundError: If no artifact with that id exists.
    """
    artifact = db.get(Artifact, artifact_id)
    if artifact is None:
        raise NotFoundError(f"Artifact '{artifact_id}' not found")
    return artifact
