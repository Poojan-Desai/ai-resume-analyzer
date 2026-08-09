# AI Career Assistant

A full-stack portfolio project for organizing a job search: upload a PDF or DOCX resume, compare it with saved job descriptions, generate structured feedback and cover-letter drafts, and track applications from one dashboard.

> **Project status:** working local prototype. The core upload, parsing, persistence, application-tracking, and UI flows are implemented. AI features require the user's own OpenAI API key. This repository does not include authentication or production-grade handling for sensitive resume data.

## What it demonstrates

- React and TypeScript single-page application with typed API responses
- FastAPI REST endpoints and Pydantic request/response validation
- SQLAlchemy models for resumes, jobs, AI artifacts, and applications
- Server-side PDF/DOCX text extraction
- Server-only OpenAI integration for resume feedback, job matching, skill-gap suggestions, and cover-letter drafts
- SQLite for local development, with a configurable database URL
- Automated backend API/parser tests plus frontend lint and production build checks

## Architecture

```text
React + TypeScript SPA
        │  /api/*
        ▼
FastAPI routers ───────────────┐
        │                      │
        ├── SQLAlchemy ──> SQLite / configurable database
        ├── pypdf / docx ─> extracted resume text
        └── AI service ───> OpenAI API (only when requested)
```

In development, Vite proxies `/api/*` to FastAPI. The API key stays in the backend environment and is never sent to the browser.

## Implemented flows

| Area | Current behavior |
|---|---|
| Resumes | Upload PDF/DOCX, extract text, list saved files, view a text preview |
| Resume review | Request structured strengths, weaknesses, improvements, score, and summary |
| Jobs | Save job descriptions and compare one with a stored resume |
| Writing support | Generate a draft cover letter grounded in supplied resume/job text |
| Skill gaps | Request missing-skill and learning-priority suggestions |
| Applications | Create, view, update, and delete application records |
| Dashboard | Show record counts, recent feedback, recent matches, and status totals |

AI output is model-generated guidance, not a deterministic hiring score. Users should verify every suggestion and generated draft.

## Local setup

Prerequisites: Python 3.11+ and a current Node.js 20 or 22 release.

### 1. Backend

```bash
cd backend
cp .env.example .env
# Add your own OPENAI_API_KEY to .env for AI endpoints.
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend

```bash
cd frontend
npm ci
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

## Configuration

| Location | Variable | Purpose |
|---|---|---|
| `backend/.env` | `OPENAI_API_KEY` | Enables AI endpoints; no key is committed |
| `backend/.env` | `DATABASE_URL` | Optional; defaults to local SQLite |
| `backend/.env` | `CORS_ORIGINS` | Comma-separated allowed frontend origins |
| `frontend/.env` | `VITE_API_URL` | Public backend origin for a deployed frontend |

## API overview

| Method | Path | Description |
|---|---|---|
| POST | `/api/resumes/upload` | Parse and store a PDF/DOCX resume |
| GET | `/api/resumes` | List stored resumes |
| POST | `/api/resumes/{id}/analyze` | Request AI resume feedback |
| POST | `/api/jobs` | Save a job posting |
| POST | `/api/jobs/{id}/match` | Request resume/job comparison |
| POST | `/api/jobs/{id}/cover-letter` | Generate a cover-letter draft |
| POST | `/api/jobs/{id}/skill-gap` | Request a skill-gap analysis |
| CRUD | `/api/applications` | Manage application records |
| GET | `/api/dashboard` | Return dashboard aggregates |

## Verification

Backend:

```bash
cd backend
pip install -r requirements-dev.txt
pytest -q
```

Frontend:

```bash
cd frontend
npm ci
npm run lint
npm run build
```

## Security and privacy boundaries

- This is a single-user local prototype; API routes are not authenticated.
- Resume text and generated artifacts are stored unencrypted in the configured database.
- Resume/job text is sent to OpenAI only when an AI action is explicitly requested.
- Do not deploy with real personal data until authentication, authorization, retention controls, encryption, rate limiting, and production secret management are added.

## Next engineering steps

- Add user authentication and per-user authorization
- Replace development table creation with database migrations
- Validate model output against strict schemas and add retry/error handling
- Add encrypted object storage and data-retention controls
- Add integration tests with a mocked AI provider

## License

MIT. See [LICENSE](LICENSE).
