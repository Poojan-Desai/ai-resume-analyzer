def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


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
