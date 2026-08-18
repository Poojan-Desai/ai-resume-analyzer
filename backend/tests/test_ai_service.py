from types import SimpleNamespace

import httpx
import openai
import pytest

from app.schemas import (
    CoverLetterDraft,
    JobMatchResult,
    ResumeAnalysisResult,
    SkillGapResult,
)
from app.services import ai_service


class FakeResponses:
    def __init__(self, output):
        self.output = output
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)
        schema = kwargs["text_format"]
        return SimpleNamespace(
            id="resp_test",
            output_parsed=schema.model_validate(self.output),
            usage=SimpleNamespace(input_tokens=120, output_tokens=80),
        )


def install_fake_client(monkeypatch, output):
    responses = FakeResponses(output)
    monkeypatch.setattr(
        ai_service, "_client", lambda: SimpleNamespace(responses=responses)
    )
    return responses


def test_resume_analysis_uses_responses_api_and_documented_schema(monkeypatch) -> None:
    responses = install_fake_client(
        monkeypatch,
        {
            "strengths": ["Evidence-backed projects"],
            "weaknesses": [],
            "improvements": ["Quantify verified outcomes"],
            "overall_score": 88,
            "summary": "Strong technical portfolio.",
        },
    )

    result = ai_service.analyze_resume("resume text", "Data analyst")

    assert result["overall_score"] == 88
    assert responses.calls[0]["text_format"] is ResumeAnalysisResult
    assert responses.calls[0]["model"] == ai_service.settings.openai_model
    assert responses.calls[0]["store"] is False
    assert responses.calls[0]["max_output_tokens"] == 2000
    assert "Data analyst" in responses.calls[0]["input"][1]["content"]


@pytest.mark.parametrize(
    ("operation", "output", "schema"),
    [
        (
            lambda: ai_service.match_resume_to_job("resume", "job"),
            {
                "score": 75,
                "matched_keywords": ["Python"],
                "gaps": ["AWS"],
                "summary": "Relevant experience.",
            },
            JobMatchResult,
        ),
        (
            lambda: ai_service.skill_gap_analysis("resume", "job"),
            {
                "missing_skills": ["dbt"],
                "suggested_resources": ["Build one tested dbt model"],
                "priority_order": ["dbt"],
            },
            SkillGapResult,
        ),
        (
            lambda: ai_service.generate_cover_letter(
                "resume", "job", "Example", "Analyst"
            ),
            {"content": "Dear Hiring Team,\n\nA grounded draft."},
            CoverLetterDraft,
        ),
    ],
)
def test_every_ai_workflow_uses_a_validated_schema(
    monkeypatch, operation, output, schema
) -> None:
    responses = install_fake_client(monkeypatch, output)

    result = operation()

    assert responses.calls[0]["text_format"] is schema
    assert result


def test_structured_output_rejects_out_of_range_or_extra_fields(monkeypatch) -> None:
    install_fake_client(
        monkeypatch,
        {
            "score": 140,
            "matched_keywords": ["Python"],
            "gaps": [],
            "summary": "Invalid score.",
            "untrusted_extra": "must not be persisted",
        },
    )

    with pytest.raises(ai_service.AIServiceError, match="invalid structured result"):
        ai_service.match_resume_to_job("resume", "job")


def test_missing_key_returns_safe_configuration_error(monkeypatch) -> None:
    monkeypatch.setattr(ai_service.settings, "openai_api_key", "")

    with pytest.raises(
        ai_service.AIServiceError, match="OpenAI is not configured"
    ) as exc:
        ai_service._client()

    assert exc.value.unavailable is True


def test_client_configures_bounded_timeout_and_retries(monkeypatch) -> None:
    captured = {}
    monkeypatch.setattr(ai_service.settings, "openai_api_key", "test-placeholder")
    monkeypatch.setattr(ai_service.settings, "openai_timeout_seconds", 12.5)
    monkeypatch.setattr(ai_service.settings, "openai_max_retries", 1)
    monkeypatch.setattr(
        ai_service,
        "OpenAI",
        lambda **kwargs: captured.update(kwargs) or SimpleNamespace(),
    )

    ai_service._client()

    assert captured["timeout"] == 12.5
    assert captured["max_retries"] == 1
    assert captured["api_key"] == "test-placeholder"


def test_provider_timeout_is_sanitized(monkeypatch) -> None:
    timeout = openai.APITimeoutError(
        request=httpx.Request("POST", "https://example.test")
    )
    monkeypatch.setattr(
        ai_service,
        "_client",
        lambda: SimpleNamespace(
            responses=SimpleNamespace(
                parse=lambda **_kwargs: (_ for _ in ()).throw(timeout)
            )
        ),
    )

    with pytest.raises(ai_service.AIServiceError, match="timed out") as exc:
        ai_service.analyze_resume("resume")

    assert exc.value.code == "OPENAI_TIMEOUT"
    assert "example.test" not in str(exc.value)


def test_empty_provider_result_is_not_persistable(monkeypatch) -> None:
    monkeypatch.setattr(
        ai_service,
        "_client",
        lambda: SimpleNamespace(
            responses=SimpleNamespace(
                parse=lambda **_kwargs: SimpleNamespace(output_parsed=None)
            )
        ),
    )

    with pytest.raises(ai_service.AIServiceError, match="no usable result"):
        ai_service.analyze_resume("resume")
