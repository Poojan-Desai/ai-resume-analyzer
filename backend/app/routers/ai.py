"""AI readiness, privacy-safe usage history, cancellation, and live verification."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import AIRequest
from app.schemas import (
    AIRequestOut,
    AIStatusOut,
    LiveCheckBody,
    LiveCheckResult,
)
from app.services import ai_service, ai_usage

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status", response_model=AIStatusOut)
def get_status(db: Session = Depends(get_db)):
    return ai_usage.status(db)


@router.get("/requests", response_model=list[AIRequestOut])
def list_requests(db: Session = Depends(get_db)):
    rows = db.query(AIRequest).order_by(AIRequest.created_at.desc()).limit(50).all()
    return [ai_usage.request_payload(row) for row in rows]


@router.post("/requests/{request_uid}/cancel", response_model=AIRequestOut)
def cancel_request(request_uid: str, db: Session = Depends(get_db)):
    try:
        row = ai_usage.request_cancellation(db, request_uid)
    except ai_usage.AIUsageError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return ai_usage.request_payload(row)


@router.post("/live-check", response_model=LiveCheckResult)
def live_check(body: LiveCheckBody, db: Session = Depends(get_db)):
    try:
        result = ai_service.execute_live_check(
            db, request_uid=str(body.request_id), consent=body.consent
        )
    except ai_service.AIServiceError as exc:
        raise HTTPException(
            status_code=ai_service.http_status_for_error(exc), detail=str(exc)
        ) from exc
    return {
        "ok": result.payload.get("status") == "ok",
        "message": "OpenAI live check succeeded.",
        "execution": result.execution,
    }
