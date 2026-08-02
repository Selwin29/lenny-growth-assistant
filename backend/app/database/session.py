"""
SQLAlchemy database setup.

Defines the engine, session factory, and declarative base used across
the application. Model classes (see app.models) import `Base` from
here and inherit from it.
"""

import logging
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLite requires this extra connect arg when used with multiple threads
# (as FastAPI's threaded request handling does). It's a no-op for other
# database backends (Postgres, MySQL, etc.).
_connect_args = {"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    """Declarative base class for all ORM models."""

    pass


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency that yields a database session.

    Ensures the session is always closed after the request finishes,
    even if an exception is raised.

    Usage:
        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
