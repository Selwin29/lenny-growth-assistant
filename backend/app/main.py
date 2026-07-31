"""
Application entrypoint.

Defines the FastAPI app factory (`create_app`) and exposes a module-level
`app` instance for ASGI servers (uvicorn app.main:app).
"""

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_v1_router
from app.api.routes.health import router as health_router
from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.core.logging_config import configure_logging

configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup/shutdown logic."""
    logger.info(
        "%s v%s starting up (environment=%s)",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.ENVIRONMENT,
    )
    yield
    logger.info("%s shutting down", settings.APP_NAME)


def create_app() -> FastAPI:
    """Application factory.

    Builds and configures the FastAPI application: metadata, middleware,
    exception handlers, and route registration. Using a factory (rather
    than a bare module-level app) keeps startup logic testable and
    avoids import-order side effects.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Backend API for the Lenny Growth Assistant — an AI-powered "
            "product growth assistant."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    # --- CORS ---
    # Production-friendly: explicit allow-list from settings rather than "*".
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # --- Centralized error handling ---
    register_exception_handlers(app)

    # --- Routes ---
    # Health check is mounted at the root (unversioned) since it's an
    # infrastructure-level endpoint, not a versioned business API.
    app.include_router(health_router)
    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
