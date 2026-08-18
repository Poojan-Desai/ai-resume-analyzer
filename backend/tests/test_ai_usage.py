import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.services import ai_usage


@pytest.fixture()
def db(tmp_path):
    database_path = tmp_path / "usage.db"
    engine = create_engine(f"sqlite:///{database_path}")
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session, engine
    finally:
        session.close()
        engine.dispose()


def enable_small_openai_budget(monkeypatch) -> None:
    monkeypatch.setattr(ai_usage.settings, "openai_api_key", "test-placeholder")
    monkeypatch.setattr(ai_usage.settings, "openai_monthly_budget_cents", 25)
    monkeypatch.setattr(ai_usage.settings, "openai_monthly_request_limit", 2)


def test_usage_record_persists_consent_fingerprint_and_metering(
    db, monkeypatch
) -> None:
    session, engine = db
    enable_small_openai_budget(monkeypatch)
    row = ai_usage.reserve_openai_request(
        session,
        request_uid="00000000-0000-4000-8000-000000000001",
        operation="LIVE_CHECK",
        prompt="bounded prompt",
        consent=True,
        max_output_tokens=100,
    )
    assert row.status == "RUNNING"
    assert row.consented_at is not None
    assert len(row.input_fingerprint) == 64
    assert not hasattr(row, "prompt")

    saved = ai_usage.complete_request(
        session,
        row,
        response_id="resp_test",
        input_tokens=40,
        output_tokens=5,
    )
    assert saved.status == "COMPLETED"
    assert saved.actual_cost_micros == ai_usage.calculate_cost_micros(40, 5)

    session.close()
    reopened = sessionmaker(bind=engine)()
    try:
        persisted = (
            reopened.query(type(row)).filter_by(request_uid=row.request_uid).one()
        )
        assert persisted.response_id == "resp_test"
        assert persisted.status == "COMPLETED"
    finally:
        reopened.close()


def test_budget_and_request_limit_block_before_another_provider_call(
    db, monkeypatch
) -> None:
    session, _ = db
    enable_small_openai_budget(monkeypatch)
    monkeypatch.setattr(ai_usage.settings, "openai_monthly_request_limit", 1)
    ai_usage.reserve_openai_request(
        session,
        request_uid="00000000-0000-4000-8000-000000000002",
        operation="RESUME_ANALYSIS",
        prompt="first",
        consent=True,
        max_output_tokens=100,
    )
    first = (
        session.query(ai_usage.AIRequest)
        .filter_by(request_uid="00000000-0000-4000-8000-000000000002")
        .one()
    )
    ai_usage.mark_request_fallback(session, first, "OPENAI_TIMEOUT")

    with pytest.raises(ai_usage.AIUsageError, match="request limit") as exc:
        ai_usage.reserve_openai_request(
            session,
            request_uid="00000000-0000-4000-8000-000000000003",
            operation="RESUME_ANALYSIS",
            prompt="second",
            consent=True,
            max_output_tokens=100,
        )
    assert exc.value.code == "OPENAI_REQUEST_LIMIT"


def test_cancellation_discards_output_and_restart_reconciles_running_rows(
    db, monkeypatch
) -> None:
    session, _ = db
    enable_small_openai_budget(monkeypatch)
    cancelled = ai_usage.reserve_openai_request(
        session,
        request_uid="00000000-0000-4000-8000-000000000004",
        operation="JOB_MATCH",
        prompt="cancel me",
        consent=True,
        max_output_tokens=100,
    )
    ai_usage.request_cancellation(session, cancelled.request_uid)
    cancelled = ai_usage.complete_request(
        session,
        cancelled,
        response_id="must-not-be-saved",
        input_tokens=10,
        output_tokens=10,
    )
    assert cancelled.status == "CANCELLED"
    assert cancelled.response_id is None
    assert cancelled.actual_cost_micros is None

    interrupted = ai_usage.reserve_openai_request(
        session,
        request_uid="00000000-0000-4000-8000-000000000005",
        operation="SKILL_GAP",
        prompt="interrupt me",
        consent=True,
        max_output_tokens=100,
    )
    assert ai_usage.reconcile_interrupted_requests(session) == 1
    session.refresh(interrupted)
    assert interrupted.status == "INTERRUPTED"
    assert interrupted.error_code == "INTERRUPTED_AFTER_RESTART"
