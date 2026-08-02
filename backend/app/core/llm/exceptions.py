from app.core.exceptions import AppException

class LLMError(AppException):
    """Base exception for all LLM related errors."""
    def __init__(self, message: str = "LLM provider error occurred", status_code: int = 502) -> None:
        super().__init__(message=message, status_code=status_code)

class LLMConfigurationError(LLMError):
    """Exception raised when LLM is configured incorrectly or keys are missing."""
    def __init__(self, message: str = "LLM configuration error") -> None:
        super().__init__(message=message, status_code=500)

class LLMProviderConnectionError(LLMError):
    """Exception raised when the LLM service is offline or unreachable."""
    def __init__(self, message: str = "Could not connect to LLM provider") -> None:
        super().__init__(message=message, status_code=502)

class LLMTimeoutError(LLMError):
    """Exception raised when the LLM request times out."""
    def __init__(self, message: str = "LLM provider request timed out") -> None:
        super().__init__(message=message, status_code=504)
