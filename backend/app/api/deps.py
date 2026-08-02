"""
Shared FastAPI dependencies for route handlers.
"""

import uuid
import logging
from fastapi import Depends, HTTPException, status, Request
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.user import User
from app.services.user_service import get_or_create_default_user, get_user
from app.services.auth_service import decode_access_token
from app.core.config import settings

logger = logging.getLogger(__name__)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Resolve the authenticated user from the Authorization header.

    If no token is provided and we are in development, falls back to the
    default development user (dev@example.com) to support legacy test scripts
    and unauthenticated client tests.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        # Fallback to dev user in development environment
        if settings.ENVIRONMENT == "development":
            return get_or_create_default_user(db)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
        )

    try:
        scheme, token = auth_header.split()
        if scheme.lower() != "bearer":
            raise ValueError()
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme. Must be Bearer <token>",
        )

    claims = decode_access_token(token)
    if not claims or "sub" not in claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token or expired session",
        )

    try:
        user_id = uuid.UUID(claims["sub"])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed token subject",
        )

    user = get_user(db, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return user
