"""
Application configuration loaded from environment variables.
Uses pydantic-settings so values can be overridden via .env file.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server and integration settings."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    # OpenAI — required for AI features (set in .env)
    openai_api_key: str = Field(default="", repr=False)
    openai_model: str = "gpt-5.6-luna"
    openai_timeout_seconds: float = Field(default=30.0, ge=1.0, le=120.0)
    openai_max_retries: int = Field(default=2, ge=0, le=5)
    openai_max_output_tokens: int = Field(default=2000, ge=100, le=8000)
    openai_monthly_budget_cents: int = Field(default=0, ge=0, le=100_000)
    openai_monthly_request_limit: int = Field(default=20, ge=1, le=1000)
    openai_input_usd_per_million_tokens: float = Field(default=0.2, gt=0, le=1000)
    openai_output_usd_per_million_tokens: float = Field(default=1.2, gt=0, le=1000)

    # SQLite path by default; can switch to postgresql+psycopg2://... later
    database_url: str = "sqlite:///./career_assistant.db"

    # Max upload size in bytes (e.g. 5 MB)
    max_upload_bytes: int = 5 * 1024 * 1024

    # CORS — frontend dev server; add production URL when you deploy
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


settings = Settings()
