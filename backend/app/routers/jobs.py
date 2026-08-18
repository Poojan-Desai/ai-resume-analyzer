"""
Job postings and AI features that pair a resume with a job description.
"""

import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import CoverLetter, JobMatch, JobPosting, Resume, SkillGapAnalysis
from app.schemas import (
    AIExecutionOut,
    CoverLetterBody,
    CoverLetterOut,
    JobCreate,
    JobMatchBody,
    JobMatchOut,
    JobOut,
    SkillGapBody,
    SkillGapOut,
)
from app.services import ai_service

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post("", response_model=JobOut)
def create_job(body: JobCreate, db: Session = Depends(get_db)):
    """Save a job title, company, and full job description text."""
    row = JobPosting(
        title=body.title, company=body.company, description=body.description
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("", response_model=list[JobOut])
def list_jobs(db: Session = Depends(get_db)):
    return db.query(JobPosting).order_by(JobPosting.created_at.desc()).all()


@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    row = db.get(JobPosting, job_id)
    if not row:
        raise HTTPException(status_code=404, detail="Job not found.")
    return row


def _match_to_schema(m: JobMatch) -> JobMatchOut:
    data = json.loads(m.payload_json)
    return JobMatchOut(
        id=m.id,
        resume_id=m.resume_id,
        job_id=m.job_id,
        score=float(m.score),
        matched_keywords=data.get("matched_keywords") or [],
        gaps=data.get("gaps") or [],
        summary=data.get("summary") or "",
        created_at=m.created_at,
    )


@router.post("/{job_id}/match", response_model=JobMatchOut)
def match_resume(
    job_id: int,
    body: JobMatchBody,
    db: Session = Depends(get_db),
):
    """Compare resume to this job: score, keywords, gaps."""
    job = db.get(JobPosting, job_id)
    resume = db.get(Resume, body.resume_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    try:
        result = ai_service.execute_job_match(
            db,
            request_uid=str(body.request_id),
            provider=body.provider,
            consent=body.consent,
            allow_local_fallback=body.allow_local_fallback,
            resume_id=resume.id,
            job_id=job.id,
            resume_text=resume.extracted_text,
            job_description=job.description,
        )
    except ai_service.AIServiceError as e:
        raise HTTPException(
            status_code=ai_service.http_status_for_error(e), detail=str(e)
        ) from e

    score = float(result.payload.get("score") or 0)
    row = JobMatch(
        resume_id=resume.id,
        job_id=job.id,
        score=score,
        payload_json=json.dumps(result.payload),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    output = _match_to_schema(row)
    output.execution = AIExecutionOut.model_validate(result.execution)
    return output


@router.post("/{job_id}/cover-letter", response_model=CoverLetterOut)
def cover_letter(
    job_id: int,
    body: CoverLetterBody,
    db: Session = Depends(get_db),
):
    """Generate a tailored cover letter."""
    job = db.get(JobPosting, job_id)
    resume = db.get(Resume, body.resume_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    try:
        result = ai_service.execute_cover_letter(
            db,
            request_uid=str(body.request_id),
            provider=body.provider,
            consent=body.consent,
            allow_local_fallback=body.allow_local_fallback,
            resume_id=resume.id,
            job_id=job.id,
            resume_text=resume.extracted_text,
            job_description=job.description,
            company=job.company or "the company",
            role_title=job.title or "the role",
            tone=body.tone,
        )
    except ai_service.AIServiceError as e:
        raise HTTPException(
            status_code=ai_service.http_status_for_error(e), detail=str(e)
        ) from e

    row = CoverLetter(
        resume_id=resume.id, job_id=job.id, content=str(result.payload["content"])
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return CoverLetterOut(
        id=row.id,
        resume_id=row.resume_id,
        job_id=row.job_id,
        content=row.content,
        created_at=row.created_at,
        execution=AIExecutionOut.model_validate(result.execution),
    )


def _skill_to_schema(s: SkillGapAnalysis) -> SkillGapOut:
    data = json.loads(s.payload_json)
    return SkillGapOut(
        id=s.id,
        resume_id=s.resume_id,
        job_id=s.job_id,
        missing_skills=data.get("missing_skills") or [],
        suggested_resources=data.get("suggested_resources") or [],
        priority_order=data.get("priority_order") or [],
        created_at=s.created_at,
    )


@router.post("/{job_id}/skill-gap", response_model=SkillGapOut)
def skill_gap(
    job_id: int,
    body: SkillGapBody,
    db: Session = Depends(get_db),
):
    """List missing skills and learning suggestions."""
    job = db.get(JobPosting, job_id)
    resume = db.get(Resume, body.resume_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found.")
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found.")

    try:
        result = ai_service.execute_skill_gap(
            db,
            request_uid=str(body.request_id),
            provider=body.provider,
            consent=body.consent,
            allow_local_fallback=body.allow_local_fallback,
            resume_id=resume.id,
            job_id=job.id,
            resume_text=resume.extracted_text,
            job_description=job.description,
        )
    except ai_service.AIServiceError as e:
        raise HTTPException(
            status_code=ai_service.http_status_for_error(e), detail=str(e)
        ) from e

    row = SkillGapAnalysis(
        resume_id=resume.id,
        job_id=job.id,
        payload_json=json.dumps(result.payload),
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    output = _skill_to_schema(row)
    output.execution = AIExecutionOut.model_validate(result.execution)
    return output


@router.get("/{job_id}/matches", response_model=list[JobMatchOut])
def list_matches(job_id: int, db: Session = Depends(get_db)):
    if not db.get(JobPosting, job_id):
        raise HTTPException(status_code=404, detail="Job not found.")
    rows = (
        db.query(JobMatch)
        .filter(JobMatch.job_id == job_id)
        .order_by(JobMatch.created_at.desc())
        .all()
    )
    return [_match_to_schema(m) for m in rows]
