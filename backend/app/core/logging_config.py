"""
Centralized logging configuration for the backend.

Call `configure_logging()` once at application startup (done in
app.main.create_app) to set up consistent, readable logging across
the whole codebase.
"""

import logging
import sys

from app.core.config import settings


def configure_logging() -> None:
    """Configure the root logger for the application.

    Uses a single stream handler writing to stdout with a consistent
    format. Log level is controlled via the LOG_LEVEL setting.
    """
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Avoid duplicate handlers if configure_logging() is called more than once
    # (e.g. during tests or module reloads).
    root_logger.handlers.clear()
    root_logger.addHandler(handler)

    # Quiet down noisy third-party loggers while keeping our own app logs verbose.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
