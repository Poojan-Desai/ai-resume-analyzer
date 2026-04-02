"""
Resume upload, listing, and AI feedback endpoints.
"""

import json
from typing import Annotated

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models import Resume, ResumeFeedback
from app.schemas import ResumeAnalyzeBody, ResumeFeedbackOut, ResumeListItem, ResumeOut
from app.services import ai_service
from app.services.resume_parser import ResumeParseError, extract_resume_text

router = APIRouter(prefix="/resumes", tags=["resumes"])


@router.post("/upload", response_model=ResumeOut)
async def upload_resume(
    file: Annotated[UploadFile, File(description="PDF or DOCX resume")],
    db: Session = Depends(get_db),
):
    """
    Accept a resume file, extract text, and persist a Resume row.
    """
    data = await file.read()
    if len(data) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File too large.")

    if not file.filename:
        raise HTTPException(status_code=400, detail="Filename is required.")

    try:
        text = extract_resume_text(file.filename, data)
    except ResumeParseError as e:
        raise HTTPException(status_code=400, detail=str(e))

    row = Resume(filename=file.filename, extracted_text=text)
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[ResumeListItem])
def list_resumes(db: Session = Depends(get_db)):
    """List uploaded resumes (metadata only, no full text in list)."""
    rows = db.query(Resume).order_by(Resume.created_at.desc()).all()
    return rows


@router.get("/{resume_id}", response_model=ResumeOut)
def get_resume(resume_id: int, db: Session = Depends(get_db)):
    """Return one resume including extracted text."""
    row = db.get(Resume, resume_id)
    if not row:
        raise HTTPException(status_code=404, detail="Resume not found.")
    return row


def _feedback_to_schema(fb: ResumeFeedback) -> ResumeFeedbackOut:
    data = json.loads(fb.payload_json)
    return ResumeFeedbackOut(
        id=fb.id,
        resume_id=fb.resume_id,
        strengths=data.get("strengths") or [],
        weaknesses=data.get("weaknesses") or [],
        improvements=data.get("improvements") or [],
        overall_score=float(data.get("overall_score") or 0),
        summary=data.get("summary") or "",
        created_at=fb.created_at,
    )


@router.post("/{resume_id}/analyze", response_model=ResumeFeedbackOut)
def analyze_resume_endpoint(
    resume_id: int,
    body: ResumeAnalyzeBody | None = None,
    db: Session = Depends(get_db),
):
    """
    Run AI resume review: strengths, weaknesses, improvements, score.
    """
    row = db.get(Resume, resume_id)
    if not row:
        raise HTTPException(status_code=404, detail="Resume not found.")

    target = (body.target_role if body else "") or ""

    try:
        raw = ai_service.analyze_resume(row.extracted_text, target_role=target)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"AI request failed: {e!s}")

    fb = ResumeFeedback(resume_id=row.id, payload_json=json.dumps(raw))
    db.add(fb)
    db.commit()
    db.refresh(fb)
    return _feedback_to_schema(fb)


@router.get("/{resume_id}/feedbacks", response_model=list[ResumeFeedbackOut])
def list_feedbacks(resume_id: int, db: Session = Depends(get_db)):
    """History of AI feedback runs for a resume."""
    row = db.get(Resume, resume_id)
    if not row:
        raise HTTPException(status_code=404, detail="Resume not found.")

    items = (
        db.query(ResumeFeedback)
        .filter(ResumeFeedback.resume_id == resume_id)
        .order_by(ResumeFeedback.created_at.desc())
        .all()
    )
    return [_feedback_to_schema(fb) for fb in items]
