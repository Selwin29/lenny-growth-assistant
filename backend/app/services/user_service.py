"""Service layer for User CRUD operations.

No authentication/password logic here — that arrives in a later
milestone. This service exists so ChatSessions have a valid owner and
so a "current user" can be resolved for now via `get_or_create_default_user`.
"""

import logging
import uuid

from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user import UserCreate

logger = logging.getLogger(__name__)

DEFAULT_DEV_EMAIL = "dev@example.com"


def get_user(db: Session, user_id: uuid.UUID) -> User | None:
    """Fetch a single user by id, or None if not found."""
    return db.get(User, user_id)


def get_user_by_email(db: Session, email: str) -> User | None:
    """Fetch a single user by email, or None if not found."""
    return db.query(User).filter(User.email == email).first()


def create_user(db: Session, payload: UserCreate) -> User:
    """Create and persist a new User."""
    user = User(email=payload.email, full_name=payload.full_name)
    db.add(user)
    db.commit()
    db.refresh(user)
    logger.info("Created user id=%s email=%s", user.id, user.email)
    return user


def get_or_create_default_user(db: Session) -> User:
    """Return the placeholder "current user" used until auth is implemented.

    Chat sessions must belong to a user, but Milestone 3 explicitly
    excludes authentication. This resolves a single, stable dev user
    (created on first use) so the rest of the chat API has a real
    owner to attach sessions to.
    """
    user = get_user_by_email(db, DEFAULT_DEV_EMAIL)
    if user is not None:
        return user
    return create_user(db, UserCreate(email=DEFAULT_DEV_EMAIL, full_name="Development User"))
