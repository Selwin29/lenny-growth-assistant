"""
Centralized exception handlers.

Registered on the FastAPI app instance so every error in the codebase
returns a consistent, meaningful JSON error shape instead of leaking
stack traces or default framework responses.
"""

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.exceptions import AppException

logger = logging.getLogger(__name__)


def _error_response(message: str, status_code: int, details=None) -> JSONResponse:
    """Build a consistent JSON error payload."""
    body = {"success": False, "error": {"message": message}}
    if details is not None:
        body["error"]["details"] = details
    return JSONResponse(status_code=status_code, content=body)


def register_exception_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to the given FastAPI app instance."""

    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        """Handle known, application-raised exceptions."""
        logger.warning("AppException on %s: %s", request.url.path, exc.message)
        return _error_response(exc.message, exc.status_code)

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Handle Pydantic/FastAPI request validation errors."""
        logger.info("Validation error on %s: %s", request.url.path, exc.errors())
        return _error_response(
            message="Request validation failed",
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            details=exc.errors(),
        )

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        """Handle standard HTTP exceptions (404, 405, etc.)."""
        logger.info("HTTPException on %s: %s", request.url.path, exc.detail)
        return _error_response(message=str(exc.detail), status_code=exc.status_code)

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Catch-all for any unexpected exception.

        Logs the full traceback server-side but returns a safe, generic
        message to the client so internals are never leaked.
        """
        logger.exception("Unhandled exception on %s", request.url.path)
        return _error_response(
            message="Internal server error",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
