"""Persistent, privacy-safe OpenAI consent, budget, usage, and recovery records."""

from __future__ import annotations

from datetime import UTC, datetime
from hashlib import sha256
from math import ceil
from threading import Lock

from sqlalchemy.orm import Session

from app.config import settings
from app.models import AIRequest

MICROS_PER_CENT = 10_000
_reservation_lock = Lock()


class AIUsageError(RuntimeError):
    """A safe preflight failure with a stable machine-readable code."""

    def __init__(self, message: str, code: str) -> None:
        super().__init__(message)
        self.code = code


def utc_now() -> datetime:
    """Return a naive UTC timestamp for SQLite compatibility."""
    return datetime.now(UTC).replace(tzinfo=None)


def month_start(now: datetime | None = None) -> datetime:
    current = now or utc_now()
    return datetime(current.year, current.month, 1)


def estimate_input_tokens(prompt: str) -> int:
    # Character estimation plus headroom for the JSON schema and message framing.
    return max(1, ceil(len(prompt) / 4 * 1.25) + 1000)


def calculate_cost_micros(input_tokens: int, output_tokens: int) -> int:
    return ceil(
        input_tokens * settings.openai_input_usd_per_million_tokens
        + output_tokens * settings.openai_output_usd_per_million_tokens
    )


def preflight(
    prompt: str, max_output_tokens: int | None = None
) -> dict[str, int | str]:
    output_limit = max_output_tokens or settings.openai_max_output_tokens
    input_tokens = estimate_input_tokens(prompt)
    return {
        "fingerprint": sha256(prompt.encode("utf-8")).hexdigest(),
        "estimated_input_tokens": input_tokens,
        "max_output_tokens": output_limit,
        "estimated_cost_micros": calculate_cost_micros(input_tokens, output_limit),
    }


def _charged_micros(row: AIRequest) -> int:
    return (
        row.actual_cost_micros
        if row.actual_cost_micros is not None
        else row.estimated_cost_micros
    )


def _openai_rows_this_month(db: Session) -> list[AIRequest]:
    return (
        db.query(AIRequest)
        .filter(
            AIRequest.created_at >= month_start(),
            AIRequest.requested_provider == "openai",
            AIRequest.estimated_cost_micros > 0,
        )
        .all()
    )


def _ensure_unused_request_id(db: Session, request_uid: str) -> None:
    if db.query(AIRequest).filter(AIRequest.request_uid == request_uid).first():
        raise AIUsageError(
            "That AI request ID was already used. Start a new request.",
            "REQUEST_ID_REUSED",
        )


def reserve_openai_request(
    db: Session,
    *,
    request_uid: str,
    operation: str,
    prompt: str,
    consent: bool,
    resume_id: int | None = None,
    job_id: int | None = None,
    max_output_tokens: int | None = None,
) -> AIRequest:
    if not consent:
        raise AIUsageError(
            "Confirm the OpenAI data disclosure before starting this request.",
            "OPENAI_CONSENT_REQUIRED",
        )
    if not settings.openai_api_key.strip():
        raise AIUsageError(
            "OpenAI is not configured. Add the key only to backend/.env, or use the local demo.",
            "OPENAI_NOT_CONFIGURED",
        )
    if settings.openai_monthly_budget_cents <= 0:
        raise AIUsageError(
            "OpenAI is disabled until OPENAI_MONTHLY_BUDGET_CENTS is positive.",
            "OPENAI_BUDGET_DISABLED",
        )

    estimate = preflight(prompt, max_output_tokens)
    with _reservation_lock:
        _ensure_unused_request_id(db, request_uid)
        rows = _openai_rows_this_month(db)
        if len(rows) >= settings.openai_monthly_request_limit:
            raise AIUsageError(
                "The local monthly OpenAI request limit has been reached.",
                "OPENAI_REQUEST_LIMIT",
            )
        reserved_or_spent = sum(_charged_micros(row) for row in rows)
        if (
            reserved_or_spent + int(estimate["estimated_cost_micros"])
            > settings.openai_monthly_budget_cents * MICROS_PER_CENT
        ):
            raise AIUsageError(
                "The local monthly OpenAI budget cannot cover this request.",
                "OPENAI_MONTHLY_BUDGET",
            )

        row = AIRequest(
            request_uid=request_uid,
            operation=operation,
            requested_provider="openai",
            provider_used="openai",
            model=settings.openai_model,
            status="RUNNING",
            resume_id=resume_id,
            job_id=job_id,
            consented_at=utc_now(),
            input_fingerprint=str(estimate["fingerprint"]),
            estimated_input_tokens=int(estimate["estimated_input_tokens"]),
            max_output_tokens=int(estimate["max_output_tokens"]),
            estimated_cost_micros=int(estimate["estimated_cost_micros"]),
        )
        db.add(row)
        db.commit()
        db.refresh(row)
        return row


def record_local_request(
    db: Session,
    *,
    request_uid: str,
    operation: str,
    prompt: str,
    resume_id: int | None = None,
    job_id: int | None = None,
    fallback_reason: str | None = None,
) -> AIRequest:
    _ensure_unused_request_id(db, request_uid)
    row = AIRequest(
        request_uid=request_uid,
        operation=operation,
        requested_provider="openai" if fallback_reason else "local",
        provider_used="local-fallback" if fallback_reason else "local-demo",
        model="deterministic-local-v1",
        status="FALLBACK" if fallback_reason else "COMPLETED",
        resume_id=resume_id,
        job_id=job_id,
        input_fingerprint=sha256(prompt.encode("utf-8")).hexdigest(),
        error_code=fallback_reason,
        completed_at=utc_now(),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def complete_request(
    db: Session,
    row: AIRequest,
    *,
    response_id: str,
    input_tokens: int,
    output_tokens: int,
) -> AIRequest:
    db.refresh(row)
    if row.cancel_requested_at is not None:
        row.status = "CANCELLED"
        row.error_code = "CANCELLED_BY_USER"
    else:
        row.status = "COMPLETED"
        row.response_id = response_id
        row.input_tokens = input_tokens
        row.output_tokens = output_tokens
        row.actual_cost_micros = calculate_cost_micros(input_tokens, output_tokens)
    row.completed_at = utc_now()
    db.commit()
    db.refresh(row)
    return row


def mark_request_failed(db: Session, row: AIRequest, code: str) -> AIRequest:
    db.refresh(row)
    row.status = "CANCELLED" if row.cancel_requested_at else "FAILED"
    row.error_code = "CANCELLED_BY_USER" if row.cancel_requested_at else code
    row.completed_at = utc_now()
    db.commit()
    db.refresh(row)
    return row


def mark_request_fallback(db: Session, row: AIRequest, code: str) -> AIRequest:
    db.refresh(row)
    if row.cancel_requested_at:
        row.status = "CANCELLED"
        row.error_code = "CANCELLED_BY_USER"
    else:
        row.status = "FALLBACK"
        row.provider_used = "local-fallback"
        row.error_code = code
    row.completed_at = utc_now()
    db.commit()
    db.refresh(row)
    return row


def request_cancellation(db: Session, request_uid: str) -> AIRequest:
    row = db.query(AIRequest).filter(AIRequest.request_uid == request_uid).first()
    if row is None:
        raise AIUsageError("AI request not found.", "AI_REQUEST_NOT_FOUND")
    if row.status == "RUNNING" and row.cancel_requested_at is None:
        row.cancel_requested_at = utc_now()
        db.commit()
        db.refresh(row)
    return row


def reconcile_interrupted_requests(db: Session) -> int:
    rows = db.query(AIRequest).filter(AIRequest.status == "RUNNING").all()
    now = utc_now()
    for row in rows:
        row.status = "INTERRUPTED"
        row.error_code = "INTERRUPTED_AFTER_RESTART"
        row.completed_at = now
    if rows:
        db.commit()
    return len(rows)


def status(db: Session) -> dict[str, int | str | bool]:
    rows = _openai_rows_this_month(db)
    spent = sum(_charged_micros(row) for row in rows)
    maximum = preflight("x" * 16_000)
    configured = bool(settings.openai_api_key.strip())
    return {
        "configured": configured,
        "enabled": configured and settings.openai_monthly_budget_cents > 0,
        "provider": "openai",
        "model": settings.openai_model,
        "monthly_budget_cents": settings.openai_monthly_budget_cents,
        "monthly_reserved_or_spent_cents": ceil(spent / MICROS_PER_CENT),
        "monthly_request_limit": settings.openai_monthly_request_limit,
        "requests_this_month": len(rows),
        "estimated_maximum_workflow_cents": max(
            1, ceil(int(maximum["estimated_cost_micros"]) / MICROS_PER_CENT)
        ),
        "local_demo_available": True,
    }


def execution_payload(row: AIRequest) -> dict[str, str | float | None]:
    return {
        "request_id": row.request_uid,
        "requested_provider": row.requested_provider,
        "provider_used": row.provider_used,
        "status": row.status,
        "model": row.model,
        "fallback_reason": row.error_code if row.status == "FALLBACK" else None,
        "estimated_cost_cents": row.estimated_cost_micros / MICROS_PER_CENT,
        "actual_cost_cents": (
            row.actual_cost_micros / MICROS_PER_CENT
            if row.actual_cost_micros is not None
            else None
        ),
    }


def request_payload(row: AIRequest) -> dict[str, object]:
    return {
        "request_id": row.request_uid,
        "operation": row.operation,
        "requested_provider": row.requested_provider,
        "provider_used": row.provider_used,
        "status": row.status,
        "model": row.model,
        "error_code": row.error_code,
        "consented_at": row.consented_at,
        "estimated_input_tokens": row.estimated_input_tokens,
        "max_output_tokens": row.max_output_tokens,
        "input_tokens": row.input_tokens,
        "output_tokens": row.output_tokens,
        "cancel_requested_at": row.cancel_requested_at,
        "completed_at": row.completed_at,
        "created_at": row.created_at,
        "estimated_cost_cents": row.estimated_cost_micros / MICROS_PER_CENT,
        "actual_cost_cents": (
            row.actual_cost_micros / MICROS_PER_CENT
            if row.actual_cost_micros is not None
            else None
        ),
    }
