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
    DATABASE_URL: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/lenny_growth_assistant"

    # --- LLM / Agent provider configuration ---
    LLM_PROVIDER: str = "gemini"
    OLLAMA_MODEL: str = "llama3.1:8b"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    # Generation/read timeout in seconds for local Ollama inference.
    OLLAMA_TIMEOUT: int = 300
    # Connection-establishment timeout (seconds). Keep short to fail fast.
    OLLAMA_CONNECT_TIMEOUT: int = 10
    # Maximum number of *words* per RAG chunk included in the LLM prompt.
    RAG_CHUNK_WORD_LIMIT: int = 300
    OPENAI_API_KEY: str = Field(default="")
    ANTHROPIC_API_KEY: str = Field(default="")
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL: str = "gemini-1.5-flash"


    # --- Security & Auth ---
    JWT_SECRET: str = "supersecretkeychangeinprod"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7 # 7 days

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    @property
    def cors_origins_list(self) -> List[str]:
        """Return CORS_ORIGINS as a clean list of origin strings."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def sync_database_url(self) -> str:
        """Return DATABASE_URL formatted with explicit driver for SQLAlchemy/psycopg2."""
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            return "postgresql+psycopg2://" + url[len("postgres://"):]
        elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
            return "postgresql+psycopg2://" + url[len("postgresql://"):]
        return url



@lru_cache
def get_settings() -> Settings:
    """Return a cached Settings instance.

    Using lru_cache ensures the .env file is parsed only once and the
    same Settings object is reused across the app (dependency-injection
    friendly).
    """
    return Settings()


settings = get_settings()
