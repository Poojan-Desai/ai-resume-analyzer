"""
Database models: resumes, job postings, AI artifacts, and applications.
"""

from datetime import UTC, datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


def utc_now() -> datetime:
    """Naive UTC timestamp for the existing SQLite DateTime columns."""
    return datetime.now(UTC).replace(tzinfo=None)


class Resume(Base):
    """Stored resume: original filename and extracted plain text."""

    __tablename__ = "resumes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(512))
    extracted_text: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    feedbacks = relationship(
        "ResumeFeedback", back_populates="resume", cascade="all, delete-orphan"
    )
    applications = relationship("Application", back_populates="resume")


class JobPosting(Base):
    """A job description the user wants to compare against."""

    __tablename__ = "job_postings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(512), default="Untitled role")
    company: Mapped[str] = mapped_column(String(512), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    matches = relationship(
        "JobMatch", back_populates="job", cascade="all, delete-orphan"
    )
    cover_letters = relationship(
        "CoverLetter", back_populates="job", cascade="all, delete-orphan"
    )
    skill_gaps = relationship(
        "SkillGapAnalysis", back_populates="job", cascade="all, delete-orphan"
    )
    applications = relationship("Application", back_populates="job_posting")


class ResumeFeedback(Base):
    """AI-generated resume review (one row per analysis run)."""

    __tablename__ = "resume_feedbacks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), index=True)
    # JSON string: strengths, weaknesses, improvements, overall_score
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    resume = relationship("Resume", back_populates="feedbacks")


class JobMatch(Base):
    """Match score and explanation for a resume + job pair."""

    __tablename__ = "job_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"), index=True)
    score: Mapped[float] = mapped_column(Float, default=0.0)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    job = relationship("JobPosting", back_populates="matches")


class CoverLetter(Base):
    """Generated cover letter text."""

    __tablename__ = "cover_letters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    job = relationship("JobPosting", back_populates="cover_letters")


class SkillGapAnalysis(Base):
    """Skill gap suggestions for a resume vs job."""

    __tablename__ = "skill_gap_analyses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    resume_id: Mapped[int] = mapped_column(ForeignKey("resumes.id"), index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("job_postings.id"), index=True)
    payload_json: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    job = relationship("JobPosting", back_populates="skill_gaps")


class Application(Base):
    """Simple application tracker."""

    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    company_name: Mapped[str] = mapped_column(String(512))
    role_title: Mapped[str] = mapped_column(String(512), default="")
    status: Mapped[str] = mapped_column(
        String(64), default="draft"
    )  # draft, applied, interview, offer, rejected
    notes: Mapped[str] = mapped_column(Text, default="")
    job_url: Mapped[str] = mapped_column(String(2048), default="")
    resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("resumes.id"), nullable=True
    )
    job_posting_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_postings.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )

    resume = relationship("Resume", back_populates="applications")
    job_posting = relationship("JobPosting", back_populates="applications")


class AIRequest(Base):
    """Privacy-safe audit and budget record for one local or OpenAI workflow."""

    __tablename__ = "ai_requests"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_uid: Mapped[str] = mapped_column(String(36), unique=True, index=True)
    operation: Mapped[str] = mapped_column(String(64), index=True)
    requested_provider: Mapped[str] = mapped_column(String(32))
    provider_used: Mapped[str] = mapped_column(String(64), default="local-demo")
    model: Mapped[str] = mapped_column(String(128), default="")
    status: Mapped[str] = mapped_column(String(32), default="RUNNING", index=True)
    resume_id: Mapped[int | None] = mapped_column(
        ForeignKey("resumes.id", ondelete="SET NULL"), nullable=True, index=True
    )
    job_id: Mapped[int | None] = mapped_column(
        ForeignKey("job_postings.id", ondelete="SET NULL"), nullable=True, index=True
    )
    consented_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    input_fingerprint: Mapped[str] = mapped_column(String(64))
    estimated_input_tokens: Mapped[int] = mapped_column(Integer, default=0)
    max_output_tokens: Mapped[int] = mapped_column(Integer, default=0)
    estimated_cost_micros: Mapped[int] = mapped_column(Integer, default=0)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    actual_cost_micros: Mapped[int | None] = mapped_column(Integer, nullable=True)
    response_id: Mapped[str | None] = mapped_column(String(128), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(64), nullable=True)
    cancel_requested_at: Mapped[datetime | None] = mapped_column(
        DateTime, nullable=True
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utc_now, onupdate=utc_now
    )
