"""
Pydantic schemas for request/response validation and API documentation.
"""

from datetime import datetime
from typing import Any, Literal
from uuid import UUID, uuid4

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
    description: str = Field(default="", max_length=50_000)


class JobOut(BaseModel):
    id: int
    title: str
    company: str
    description: str
    created_at: datetime

    model_config = {"from_attributes": True}


class AIRequestOptions(BaseModel):
    """Controls shared by every local-demo or OpenAI workflow."""

    request_id: UUID = Field(default_factory=uuid4)
    provider: Literal["local", "openai"] = "local"
    consent: bool = False
    allow_local_fallback: bool = True

    model_config = {"extra": "forbid"}


class AIExecutionOut(BaseModel):
    request_id: str
    requested_provider: str
    provider_used: str
    status: str
    model: str
    fallback_reason: str | None = None
    estimated_cost_cents: float = 0
    actual_cost_cents: float | None = None


# --- AI: resume feedback ---
class ResumeAnalyzeBody(AIRequestOptions):
    """Optional extra context for the reviewer."""

    target_role: str = Field(default="", max_length=500)


class ResumeAnalysisResult(BaseModel):
    """Validated model output before it is persisted as feedback."""

    strengths: list[str] = Field(max_length=20)
    weaknesses: list[str] = Field(max_length=20)
    improvements: list[str] = Field(max_length=20)
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
    execution: AIExecutionOut | None = None


# --- AI: job match ---
class JobMatchBody(AIRequestOptions):
    resume_id: int


class JobMatchResult(BaseModel):
    score: float = Field(ge=0, le=100)
    matched_keywords: list[str] = Field(max_length=30)
    gaps: list[str] = Field(max_length=30)
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
    execution: AIExecutionOut | None = None


# --- Cover letter ---
class CoverLetterBody(AIRequestOptions):
    resume_id: int
    tone: Literal["professional", "enthusiastic", "concise"] = "professional"


class CoverLetterDraft(BaseModel):
    """Validated model output before a cover letter is persisted."""

    content: str = Field(min_length=1, max_length=8000)

    model_config = {"extra": "forbid"}


class CoverLetterOut(BaseModel):
    id: int
    resume_id: int
    job_id: int
    content: str
    created_at: datetime
    execution: AIExecutionOut | None = None


# --- Skill gap ---
class SkillGapBody(AIRequestOptions):
    resume_id: int


class SkillGapResult(BaseModel):
    missing_skills: list[str] = Field(max_length=30)
    suggested_resources: list[str] = Field(max_length=30)
    priority_order: list[str] = Field(max_length=30)

    model_config = {"extra": "forbid"}


class SkillGapOut(BaseModel):
    id: int
    resume_id: int
    job_id: int
    missing_skills: list[str]
    suggested_resources: list[str]
    priority_order: list[str]
    created_at: datetime
    execution: AIExecutionOut | None = None


class LiveCheckBody(AIRequestOptions):
    """Minimal low-output provider check. OpenAI must be selected explicitly."""

    provider: Literal["openai"] = "openai"
    allow_local_fallback: bool = False


class LiveCheckResult(BaseModel):
    ok: bool
    message: str
    execution: AIExecutionOut


class AIStatusOut(BaseModel):
    configured: bool
    enabled: bool
    provider: str
    model: str
    monthly_budget_cents: int
    monthly_reserved_or_spent_cents: int
    monthly_request_limit: int
    requests_this_month: int
    estimated_maximum_workflow_cents: int
    local_demo_available: bool


class AIRequestOut(BaseModel):
    request_id: str
    operation: str
    requested_provider: str
    provider_used: str
    status: str
    model: str
    error_code: str | None
    consented_at: datetime | None
    estimated_input_tokens: int
    max_output_tokens: int
    input_tokens: int | None
    output_tokens: int | None
    cancel_requested_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    estimated_cost_cents: float
    actual_cost_cents: float | None


# --- Applications ---
class ApplicationCreate(BaseModel):
    company_name: str
    role_title: str = ""
    status: str = "draft"
    notes: str = ""
    job_url: str = ""
    resume_id: int | None = None
    job_posting_id: int | None = None


class ApplicationUpdate(BaseModel):
    company_name: str | None = None
    role_title: str | None = None
    status: str | None = None
    notes: str | None = None
    job_url: str | None = None
    resume_id: int | None = None
    job_posting_id: int | None = None


class ApplicationOut(BaseModel):
    id: int
    company_name: str
    role_title: str
    status: str
    notes: str
    job_url: str
    resume_id: int | None
    job_posting_id: int | None
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
