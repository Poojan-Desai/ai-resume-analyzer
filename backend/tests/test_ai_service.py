import pytest
from pydantic import ValidationError

from app.services import ai_service


def test_resume_analysis_accepts_only_the_documented_schema(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_service,
        "_chat_json",
        lambda *_args, **_kwargs: {
            "strengths": ["Evidence-backed projects"],
            "weaknesses": [],
            "improvements": ["Quantify verified outcomes"],
            "overall_score": 88,
            "summary": "Strong technical portfolio.",
        },
    )

    result = ai_service.analyze_resume("resume text")

    assert result["overall_score"] == 88
    assert result["strengths"] == ["Evidence-backed projects"]


def test_resume_analysis_rejects_out_of_range_scores(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_service,
        "_chat_json",
        lambda *_args, **_kwargs: {
            "strengths": [],
            "weaknesses": [],
            "improvements": [],
            "overall_score": 140,
            "summary": "Invalid score.",
        },
    )

    with pytest.raises(ValidationError):
        ai_service.analyze_resume("resume text")


def test_job_match_rejects_missing_or_extra_model_fields(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_service,
        "_chat_json",
        lambda *_args, **_kwargs: {
            "score": 75,
            "matched_keywords": ["Python"],
            "gaps": [],
            "summary": "Relevant experience.",
            "untrusted_extra": "must not be persisted",
        },
    )

    with pytest.raises(ValidationError):
        ai_service.match_resume_to_job("resume", "job")
