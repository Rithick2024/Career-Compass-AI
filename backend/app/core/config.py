"""
Centralized application configuration.

All environment-driven settings live here. Every other module should
import `settings` from this file rather than reading `os.environ`
directly, so configuration stays in one place and is validated once
at startup.
"""

from functools import lru_cache
from typing import List

from pydantic import Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Strongly-typed application settings, populated from `.env`."""

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --- App ---
    APP_NAME: str = "Career Compass AI"
    APP_ENV: str = "development"
    DEBUG: bool = True
    API_V1_PREFIX: str = "/api/v1"

    # --- Server ---
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # --- Database ---
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_DB: str

    DB_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30

    # --- CORS ---
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    # --- Logging ---
    LOG_LEVEL: str = "INFO"

    # --- JWT / Auth ---
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --- Email validation ---
    # In development/test environments, RFC 2606 reserved domains (.test)
    # can be allowed for synthetic demo accounts while preserving full syntax rules.
    # In production (APP_ENV=production), test domains are strictly disallowed.
    ALLOW_TEST_EMAIL_DOMAINS: bool = True

    # --- Resume file storage ---
    # Relative to the project root; resolved by app.modules.resumes.storage.
    # Local filesystem for this MVP — see docs/resume-module.md for the
    # planned cloud-storage migration path.
    RESUME_UPLOAD_DIR: str = "uploads/resumes"
    RESUME_MAX_FILE_SIZE_MB: int = 5

    # --- Gemini AI Configuration ---
    GEMINI_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-3.5-flash"
    GEMINI_FALLBACK_MODELS: str = "gemini-flash-lite-latest,gemini-3.6-flash"
    GEMINI_TIMEOUT_SECONDS: float = 30.0
    GEMINI_MAX_INPUT_CHARS: int = 1500
    GEMINI_MAX_OUTPUT_TOKENS: int = 1000

    @computed_field  # type: ignore[misc]
    @property
    def DATABASE_URL(self) -> str:
        """Async SQLAlchemy connection string (asyncpg driver)."""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[misc]
    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() == "production"


def configure_email_validator(app_settings: Settings | None = None) -> None:
    """
    Configures the `email-validator` library according to environment settings.

    RFC 2606 reserves `.test` (along with `.example`, `.invalid`, `.localhost`)
    for testing, documentation, and synthetic development environments.
    By default, `email-validator` rejects reserved TLDs. Setting
    `email_validator.TEST_ENVIRONMENT = True` allows these synthetic domains
    in development and test environments while strictly maintaining all
    email syntax checks, mailbox validation, and structure validation.

    In production (`app_settings.is_production` is True), `TEST_ENVIRONMENT`
    is strictly forced to `False`, rejecting all special-use/reserved domains.
    """
    try:
        import email_validator
    except ImportError:
        return

    cfg = app_settings or get_settings()
    if cfg.is_production:
        email_validator.TEST_ENVIRONMENT = False
    else:
        email_validator.TEST_ENVIRONMENT = bool(cfg.ALLOW_TEST_EMAIL_DOMAINS)


@lru_cache
def get_settings() -> Settings:
    """
    Cached settings accessor.

    Using lru_cache means `.env` is parsed once per process. FastAPI's
    dependency-injection system can also call this via `Depends`
    wherever settings are needed inside request-handling code.
    """
    return Settings()


settings = get_settings()
configure_email_validator(settings)
