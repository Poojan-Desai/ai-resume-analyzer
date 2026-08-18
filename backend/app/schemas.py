"""
Pydantic schemas for request/response validation and API documentation.
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


# --- Resume ---
class ResumeOut(BaseModel):
    id: int
    filename: str
    extracted_text: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ResumeListItem(BaseModel):
    id: int
    filename: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- Job posting ---
class JobCreate(BaseModel):
    title: str = Field(default="Untitled role", max_length=512)
    company: str = Field(default="", max_length=512)
    description: str = ""


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


# --- AI: resume feedback ---
class ResumeAnalyzeBody(BaseModel):
    """Optional extra context for the reviewer."""

    target_role: str = ""


class ResumeAnalysisResult(BaseModel):
    """Validated model output before it is persisted as feedback."""

    strengths: list[str]
    weaknesses: list[str]
    improvements: list[str]
    overall_score: float = Field(ge=0, le=100)
    summary: str = Field(min_length=1)

    model_config = {"extra": "forbid"}


class ResumeFeedbackOut(BaseModel):
    id: int
    resume_id: int
    strengths: list[str]
    weaknesses: list[str]
    improvements: list[str]
    overall_score: float
    summary: str
    created_at: datetime


# --- AI: job match ---
class JobMatchBody(BaseModel):
    resume_id: int


class JobMatchResult(BaseModel):
    score: float = Field(ge=0, le=100)
    matched_keywords: list[str]
    gaps: list[str]
    summary: str = Field(min_length=1)

    model_config = {"extra": "forbid"}


class JobMatchOut(BaseModel):
    id: int
    resume_id: int
    job_id: int
    score: float
    matched_keywords: list[str]
    gaps: list[str]
    summary: str
    created_at: datetime


# --- Cover letter ---
class CoverLetterBody(BaseModel):
    resume_id: int
    tone: str = "professional"  # professional, enthusiastic, concise


class CoverLetterOut(BaseModel):
    id: int
    resume_id: int
    job_id: int
    content: str
    created_at: datetime


# --- Skill gap ---
class SkillGapBody(BaseModel):
    resume_id: int


class SkillGapResult(BaseModel):
    missing_skills: list[str]
    suggested_resources: list[str]
    priority_order: list[str]

    model_config = {"extra": "forbid"}


class SkillGapOut(BaseModel):
    id: int
    resume_id: int
    job_id: int
    missing_skills: list[str]
    suggested_resources: list[str]
    priority_order: list[str]
    created_at: datetime


# --- Applications ---
class ApplicationCreate(BaseModel):
    company_name: str
    role_title: str = ""
    status: str = "draft"
    notes: str = ""
    job_url: str = ""
    resume_id: Optional[int] = None
    job_posting_id: Optional[int] = None


class ApplicationUpdate(BaseModel):
    company_name: Optional[str] = None
    role_title: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
    job_url: Optional[str] = None
    resume_id: Optional[int] = None
    job_posting_id: Optional[int] = None


class ApplicationOut(BaseModel):
    id: int
    company_name: str
    role_title: str
    status: str
    notes: str
    job_url: str
    resume_id: Optional[int]
    job_posting_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DashboardOut(BaseModel):
    """Aggregated stats for the home dashboard."""

    resume_count: int
    job_count: int
    application_count: int
    recent_feedbacks: list[dict[str, Any]]
    recent_matches: list[dict[str, Any]]
    applications_by_status: dict[str, int]
