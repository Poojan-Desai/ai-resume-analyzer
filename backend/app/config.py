"""
Application configuration loaded from environment variables.
Uses pydantic-settings so values can be overridden via .env file.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Server and integration settings."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # OpenAI — required for AI features (set in .env)
    openai_api_key: str = ""

    # SQLite path by default; can switch to postgresql+psycopg2://... later
    database_url: str = "sqlite:///./career_assistant.db"

    # Max upload size in bytes (e.g. 5 MB)
    max_upload_bytes: int = 5 * 1024 * 1024

    # CORS — frontend dev server; add production URL when you deploy
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"


settings = Settings()
