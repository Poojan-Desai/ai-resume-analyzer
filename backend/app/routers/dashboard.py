"""
Dashboard summary: counts and recent AI activity.
"""

import json
from collections import Counter

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Application, JobMatch, JobPosting, Resume, ResumeFeedback
from app.schemas import DashboardOut

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    resume_count = db.query(Resume).count()
    job_count = db.query(JobPosting).count()
    application_count = db.query(Application).count()

    recent_fb = (
        db.query(ResumeFeedback)
        .order_by(ResumeFeedback.created_at.desc())
        .limit(5)
        .all()
    )
    recent_feedbacks = []
    for fb in recent_fb:
        data = json.loads(fb.payload_json)
        recent_feedbacks.append(
            {
                "id": fb.id,
                "resume_id": fb.resume_id,
                "overall_score": data.get("overall_score"),
                "summary": (data.get("summary") or "")[:200],
                "created_at": fb.created_at.isoformat(),
            }
        )

    recent_m = (
        db.query(JobMatch).order_by(JobMatch.created_at.desc()).limit(5).all()
    )
    recent_matches = []
    for m in recent_m:
        data = json.loads(m.payload_json)
        recent_matches.append(
            {
                "id": m.id,
                "resume_id": m.resume_id,
                "job_id": m.job_id,
                "score": m.score,
                "summary": (data.get("summary") or "")[:200],
                "created_at": m.created_at.isoformat(),
            }
        )

    apps = db.query(Application).all()
    by_status = Counter(a.status for a in apps)

    return DashboardOut(
        resume_count=resume_count,
        job_count=job_count,
        application_count=application_count,
        recent_feedbacks=recent_feedbacks,
        recent_matches=recent_matches,
        applications_by_status=dict(by_status),
    )
