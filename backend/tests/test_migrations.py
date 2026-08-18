from sqlalchemy import create_engine, inspect, text

from app.migrations import SCHEMA_VERSION, run_migrations


def test_additive_migration_is_idempotent_and_records_version(tmp_path) -> None:
    engine = create_engine(f"sqlite:///{tmp_path / 'migration.db'}")
    run_migrations(engine)
    run_migrations(engine)

    tables = set(inspect(engine).get_table_names())
    assert {"resumes", "job_postings", "ai_requests", "schema_migrations"} <= tables
    with engine.connect() as connection:
        versions = (
            connection.execute(text("SELECT version FROM schema_migrations"))
            .scalars()
            .all()
        )
    assert versions == [SCHEMA_VERSION]
    engine.dispose()
