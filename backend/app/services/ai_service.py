"""
OpenAI API calls: structured JSON outputs for resume feedback, matching, etc.
"""

import json
from typing import Any

from openai import OpenAI

from app.config import settings
from app.schemas import JobMatchResult, ResumeAnalysisResult, SkillGapResult


def _client() -> OpenAI:
    if not settings.openai_api_key:
        raise RuntimeError("OPENAI_API_KEY is not set. Add it to backend/.env")
    return OpenAI(api_key=settings.openai_api_key)


def _chat_json(system: str, user: str, model: str = "gpt-4o-mini") -> dict[str, Any]:
    """
    Ask the model to return only valid JSON matching our schema instructions.
    """
    client = _client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.4,
        response_format={"type": "json_object"},
    )
    raw = response.choices[0].message.content or "{}"
    return json.loads(raw)


def chat_plain(system: str, user: str, model: str = "gpt-4o-mini") -> str:
    """Plain text completion (e.g. cover letter body)."""
    client = _client()
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.7,
    )
    return (response.choices[0].message.content or "").strip()


def analyze_resume(resume_text: str, target_role: str = "") -> dict[str, Any]:
    """
    Returns keys: strengths, weaknesses, improvements, overall_score (0-100), summary.
    """
    system = (
        "You are an expert technical recruiter. Respond with a single JSON object only. "
        "Keys: strengths (array of strings), weaknesses (array), improvements (array of actionable tips), "
        "overall_score (number 0-100), summary (one short paragraph). "
        "Be constructive and specific. No markdown outside JSON."
    )
    extra = f" Target role context (may be empty): {target_role}" if target_role else ""
    user = f"Resume text:\n---\n{resume_text[:12000]}\n---{extra}"
    return ResumeAnalysisResult.model_validate(_chat_json(system, user)).model_dump()


def match_resume_to_job(resume_text: str, job_description: str) -> dict[str, Any]:
    """
    Returns keys: score (0-100), matched_keywords, gaps, summary.
    """
    system = (
        "You compare a resume to a job description. Return JSON only with keys: "
        "score (0-100 number), matched_keywords (array of short strings), "
        "gaps (array of missing or weak areas), summary (2-3 sentences)."
    )
    user = (
        f"RESUME:\n{resume_text[:8000]}\n\nJOB DESCRIPTION:\n{job_description[:8000]}"
    )
    return JobMatchResult.model_validate(_chat_json(system, user)).model_dump()


def skill_gap_analysis(resume_text: str, job_description: str) -> dict[str, Any]:
    """
    Returns keys: missing_skills, suggested_resources, priority_order.
    """
    system = (
        "You identify skill gaps between a resume and a job posting. Return JSON only with keys: "
        "missing_skills (array), suggested_resources (array of short learning suggestions), "
        "priority_order (array of skill names in order to learn first)."
    )
    user = (
        f"RESUME:\n{resume_text[:8000]}\n\nJOB:\n{job_description[:8000]}"
    )
    return SkillGapResult.model_validate(_chat_json(system, user)).model_dump()


def generate_cover_letter(
    resume_text: str,
    job_description: str,
    company: str,
    role_title: str,
    tone: str = "professional",
) -> str:
    """Returns a full cover letter as plain text."""
    system = (
        f"Write a cover letter in {tone} tone. "
        "Use the resume facts only; do not invent employers or degrees. "
        "Address the role and company. No placeholder brackets like [Your Name]. "
        "Output plain text only, no JSON."
    )
    user = (
        f"Company: {company}\nRole: {role_title}\n\n"
        f"Job description:\n{job_description[:6000]}\n\n"
        f"Resume:\n{resume_text[:6000]}"
    )
    return chat_plain(system, user)
