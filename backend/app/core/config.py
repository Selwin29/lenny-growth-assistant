"""
Application configuration.

Loads settings from environment variables (and a local .env file during
development) using pydantic-settings. Import the `settings` singleton
anywhere configuration values are needed instead of reading os.environ
directly.
"""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralized application settings.

    All values can be overridden via environment variables or a `.env`
    file in the backend root. Nothing here should contain real secrets —
    see `.env.example` for the documented list of expected variables.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    # --- General application metadata ---
    APP_NAME: str = "Lenny Growth Assistant API"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # --- API ---
    API_V1_PREFIX: str = "/api/v1"

    # --- CORS ---
    # Comma-separated list of allowed origins, parsed into a list.
    CORS_ORIGINS: str = "http://localhost:5173"

    # --- Database ---
    DATABASE_URL: str = "sqlite:///./lenny_growth_assistant.db"

    # --- LLM / Agent provider configuration (used in later milestones) ---
    LLM_PROVIDER: str = "ollama"
    OLLAMA_MODEL: str = "llama3"
    OPENAI_API_KEY: str = Field(default="")
    ANTHROPIC_API_KEY: str = Field(default="")

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS_ORIGINS as a clean list of origin strings."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Using lru_cache ensures the .env file is parsed only once and the
    same Settings object is reused across the app (dependency-injection
    friendly).
    """
    return Settings()


settings = get_settings()
