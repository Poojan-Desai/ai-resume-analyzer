def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["ai"]["provider"] == "openai"
    assert payload["ai"]["configured"] is False
    assert "api_key" not in payload["ai"]


def test_job_and_application_crud(client):
    job_response = client.post(
        "/api/jobs",
        json={
            "title": "Software Engineer Intern",
            "company": "Example Co",
            "description": "Build and test Python services.",
        },
    )
    assert job_response.status_code == 200
    job = job_response.json()

    create_response = client.post(
        "/api/applications",
        json={
            "company_name": "Example Co",
            "role_title": "Software Engineer Intern",
            "status": "applied",
            "job_posting_id": job["id"],
        },
    )
    assert create_response.status_code == 200
    application = create_response.json()

    patch_response = client.patch(
        f"/api/applications/{application['id']}",
        json={"status": "interview"},
    )
    assert patch_response.status_code == 200
    assert patch_response.json()["status"] == "interview"

    dashboard_response = client.get("/api/dashboard")
    assert dashboard_response.status_code == 200
    assert dashboard_response.json()["application_count"] == 1

    delete_response = client.delete(f"/api/applications/{application['id']}")
    assert delete_response.status_code == 204


def test_resume_upload_rejects_unsupported_type(client):
    response = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.txt", b"plain text", "text/plain")},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unsupported file type. Use PDF or DOCX."


def test_all_four_local_demo_routes_persist_validated_labeled_results(
    client, monkeypatch
):
    monkeypatch.setattr(
        "app.routers.resumes.extract_resume_text",
        lambda _filename, _data: "Python and FastAPI project experience.",
    )
    resume_response = client.post(
        "/api/resumes/upload",
        files={
            "file": (
                "resume.pdf",
                b"synthetic resume bytes",
                "application/pdf",
            )
        },
    )
    assert resume_response.status_code == 200
    resume_id = resume_response.json()["id"]
    job_response = client.post(
        "/api/jobs",
        json={
            "title": "Data Analyst",
            "company": "Example Co",
            "description": "Python, SQL, AWS, and experimentation.",
        },
    )
    job_id = job_response.json()["id"]

    analysis = client.post(f"/api/resumes/{resume_id}/analyze", json={})
    match = client.post(f"/api/jobs/{job_id}/match", json={"resume_id": resume_id})
    cover = client.post(
        f"/api/jobs/{job_id}/cover-letter",
        json={"resume_id": resume_id, "tone": "professional"},
    )
    gap = client.post(f"/api/jobs/{job_id}/skill-gap", json={"resume_id": resume_id})

    assert analysis.status_code == 200
    assert analysis.json()["execution"]["provider_used"] == "local-demo"
    assert "test flow" in analysis.json()["summary"].lower()
    assert match.status_code == 200
    assert "python" in match.json()["matched_keywords"]
    assert match.json()["execution"]["provider_used"] == "local-demo"
    assert cover.status_code == 200
    assert cover.json()["content"].startswith("Dear Hiring Team")
    assert gap.status_code == 200
    assert "aws" in gap.json()["missing_skills"]

    requests = client.get("/api/ai/requests").json()
    assert len(requests) == 4
    assert {item["status"] for item in requests} == {"COMPLETED"}
    assert {item["provider_used"] for item in requests} == {"local-demo"}


def test_openai_route_requires_consent_and_has_safe_configuration_error(
    client, monkeypatch
):
    monkeypatch.setattr(
        "app.routers.resumes.extract_resume_text",
        lambda _filename, _data: "Synthetic resume.",
    )
    resume = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.pdf", b"bytes", "application/pdf")},
    ).json()

    no_consent = client.post(
        f"/api/resumes/{resume['id']}/analyze",
        json={
            "provider": "openai",
            "consent": False,
            "allow_local_fallback": False,
        },
    )
    assert no_consent.status_code == 400
    assert "disclosure" in no_consent.json()["detail"].lower()

    not_configured = client.post(
        f"/api/resumes/{resume['id']}/analyze",
        json={
            "provider": "openai",
            "consent": True,
            "allow_local_fallback": False,
        },
    )
    assert not_configured.status_code == 503
    assert "not configured" in not_configured.json()["detail"].lower()
    assert "api_key" not in not_configured.json()["detail"].lower()


def test_unconfigured_openai_can_return_an_explicit_local_fallback(client, monkeypatch):
    monkeypatch.setattr(
        "app.routers.resumes.extract_resume_text",
        lambda _filename, _data: "Python and SQL.",
    )
    resume = client.post(
        "/api/resumes/upload",
        files={"file": ("resume.pdf", b"bytes", "application/pdf")},
    ).json()

    response = client.post(
        f"/api/resumes/{resume['id']}/analyze",
        json={"provider": "openai", "consent": True},
    )

    assert response.status_code == 200
    execution = response.json()["execution"]
    assert execution["status"] == "FALLBACK"
    assert execution["provider_used"] == "local-fallback"
    assert execution["fallback_reason"] == "OPENAI_NOT_CONFIGURED"


def test_live_check_uses_budgeted_openai_path_without_a_real_call(client, monkeypatch):
    from app.services import ai_service

    monkeypatch.setattr(ai_service.settings, "openai_api_key", "test-placeholder")
    monkeypatch.setattr(ai_service.settings, "openai_monthly_budget_cents", 25)
    monkeypatch.setattr(ai_service.settings, "openai_monthly_request_limit", 20)
    monkeypatch.setattr(
        ai_service,
        "_call_structured",
        lambda *_args, **_kwargs: ai_service.ProviderResponse(
            parsed=ai_service.ProviderLiveCheck(status="ok"),
            response_id="resp_mock_live_check",
            input_tokens=30,
            output_tokens=5,
        ),
    )

    response = client.post(
        "/api/ai/live-check",
        json={"provider": "openai", "consent": True},
    )

    assert response.status_code == 200
    assert response.json()["ok"] is True
    execution = response.json()["execution"]
    assert execution["provider_used"] == "openai"
    assert execution["status"] == "COMPLETED"
    assert execution["actual_cost_cents"] is not None
