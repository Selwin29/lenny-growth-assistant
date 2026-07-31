"""Health check endpoint.

Deliberately does not touch the database so it can be used as a
lightweight liveness probe (load balancers, uptime monitors, etc.).
"""

import logging

from fastapi import APIRouter

from app.core.config import settings
from app.schemas.health import HealthResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Lightweight liveness check. Does not query the database.",
)
async def health_check() -> HealthResponse:
    """Return a simple status payload confirming the API is running."""
    logger.debug("Health check requested")
    return HealthResponse(status="healthy", service=settings.APP_NAME)
