"""
Application-level custom exceptions.

Keep exceptions here so route/service code can raise meaningful,
domain-specific errors that the centralized exception handlers
(app.core.error_handlers) know how to translate into clean JSON
responses.
"""


class AppException(Exception):
    """Base class for all application-specific exceptions.

    Attributes:
        message: Human-readable error message returned to the client.
        status_code: HTTP status code to respond with.
    """

    def __init__(self, message: str = "An unexpected error occurred", status_code: int = 500) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppException):
    """Raised when a requested resource cannot be found."""

    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, status_code=404)


class BadRequestError(AppException):
    """Raised when a request is malformed or invalid."""

    def __init__(self, message: str = "Invalid request") -> None:
        super().__init__(message=message, status_code=400)
