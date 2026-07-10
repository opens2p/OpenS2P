# OpenS2P – Configuration
# ========================
# Pydantic Settings that reads from environment variables (and .env files).
# Every setting has a sensible default for local development.

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # ── Application ───────────────────────────────────────────────────────
    APP_NAME: str = "OpenS2P API"
    APP_VERSION: str = "0.2.0"
    DEBUG: bool = False

    # ── Database ──────────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://opens2p:opens2p@localhost:5432/opens2p_dev"

    # ── Security ──────────────────────────────────────────────────────────
    JWT_SECRET_KEY: str = "opens2p-dev-secret-key-do-not-use-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60

    # ── AI / ML ──────────────────────────────────────────────────────────
    AI_PROVIDER: str = "local"
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o"
    AI_GOVERNANCE_ENABLED: bool = True
    AI_MAX_TOKENS_PER_REQUEST: int = 4096
    AI_COST_PER_1K_TOKENS: float = 0.01

    # ── Observability ─────────────────────────────────────────────────────
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: str | None = None

    # ── CORS ──────────────────────────────────────────────────────────────
    CORS_ORIGINS: list[str] = ["*"]

    # ── Rate Limiting ───────────────────────────────────────────────
    RATE_LIMIT_MAX: int = 5000
    RATE_LIMIT_WINDOW: int = 60

    # ── File Upload ─────────────────────────────────────────────────
    MAX_UPLOAD_SIZE_MB: int = 50
    UPLOAD_DIR: str = "./uploads"

    # ── Security ────────────────────────────────────────────────────
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    PASSWORD_MIN_LENGTH: int = 8
    ALLOWED_ORIGINS: list[str] = ["*"]


settings = Settings()
