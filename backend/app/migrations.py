"""Small idempotent schema migration runner for the local SQLite application."""

from sqlalchemy import Engine, text

from app import models  # noqa: F401 - registers every mapped table
from app.database import Base, engine

SCHEMA_VERSION = "2026-08-18-ai-requests-v1"


def run_migrations(bind: Engine = engine) -> None:
    """Create missing additive tables and record the applied schema version."""
    Base.metadata.create_all(bind=bind)
    with bind.begin() as connection:
        connection.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version VARCHAR(128) PRIMARY KEY,
                    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
        )
        connection.execute(
            text("INSERT OR IGNORE INTO schema_migrations (version) VALUES (:version)"),
            {"version": SCHEMA_VERSION},
        )


if __name__ == "__main__":
    run_migrations()
    print(f"Database schema is ready at {SCHEMA_VERSION}.")
