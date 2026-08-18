# AI Career Assistant

A local-first full-stack portfolio application for uploading a PDF or DOCX
resume, comparing it with saved job descriptions, drafting grounded career
materials, and tracking applications.

> **Status:** the local application and deterministic demo flow are complete and
> testable without an API key. The optional OpenAI Responses API path is wired,
> schema-validated, consent-gated, budget-limited, and usage-audited, but a live
> call still requires the user's own key and account credits. This is a
> single-user local project, not a production service for sensitive data.

## What it demonstrates

- React and TypeScript single-page application with typed API responses
- FastAPI endpoints and Pydantic request/response validation
- SQLAlchemy and SQLite persistence for resumes, jobs, applications, AI
  artifacts, and privacy-safe AI request records
- Server-side PDF/DOCX text extraction
- Four server-only OpenAI Responses API workflows: resume feedback, job
  matching, skill gaps, and cover-letter drafts
- Structured Outputs validated against strict Pydantic schemas before model
  output can be persisted
- `store=False`, bounded output, SDK timeouts/retries, safe provider errors, and
  prompt-injection boundaries for resume/job text
- Explicit per-request cloud consent, disabled-by-default monthly budget,
  request cap, conservative preflight estimate, and saved actual token usage
- A clearly labeled deterministic local demo and labeled fallback so every
  screen is testable without a key
- Cancellation flags that discard a late provider result, plus startup recovery
  that marks interrupted requests honestly after a restart

The local demo is not a language model and must not be described as one. It
exists to exercise the complete UI, validation, persistence, and error-state
flow for free.

## Architecture

```text
React + TypeScript SPA
        │  /api/*
        ▼
FastAPI routers ───────────────┐
        │                      │
        ├── SQLAlchemy ──> SQLite
        ├── pypdf / docx ─> extracted resume text
        ├── local demo ───> deterministic labeled result
        └── AI service ───> OpenAI Responses API (explicit opt-in only)
```

The API key is read only by the backend. It is never returned to the browser,
stored in SQLite, or included in an AI request record.

## Implemented flows

| Area | Current behavior |
|---|---|
| Resumes | Upload PDF/DOCX, extract text, list files, and view a text preview |
| Resume review | Local demo or consented OpenAI feedback with strict output validation |
| Jobs | Save a job and compare it with a stored resume |
| Writing support | Generate a grounded local-demo or OpenAI cover-letter draft |
| Skill gaps | Return labeled local keyword gaps or consented model suggestions |
| Applications | Create, view, update, and delete application records |
| AI controls | Readiness, budgets, request history, cancellation, fallback, and live check |

Model output is guidance, not a deterministic hiring score. Verify every claim
and draft before using it.

## Run locally on macOS

Prerequisites: Python 3.11+ and Node.js 20 or 22.

### 1. Start the backend

```bash
cd ai-resume-analyzer/backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
python -m app.migrations
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Leave `OPENAI_API_KEY` blank and `OPENAI_MONTHLY_BUDGET_CENTS=0` for the free
local demo. API documentation is at
[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 2. Start the frontend in a second Terminal window

```bash
cd ai-resume-analyzer/frontend
npm ci
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

### 3. Test the no-key flow

1. Upload a PDF or DOCX resume.
2. Keep **Local deterministic demo** selected and run resume analysis.
3. Save a job description, select the resume and job, and run all three tools.
4. Confirm every result says `local-demo`, saved results remain after refresh,
   and `GET /api/ai/requests` shows completed local records.

## Enable a minimal live OpenAI test

Never paste a key into source code, `.env.example`, chat, or a Git commit.

1. Open `backend/.env` on your Mac.
2. Set `OPENAI_API_KEY` to your project key.
3. Set a deliberately small local guard, for example
   `OPENAI_MONTHLY_BUDGET_CENTS=25` for $0.25.
4. Confirm the model and pricing variables match current official pricing for
   your selected model. The checked-in defaults match `gpt-5.6-luna` as checked
   on August 18, 2026.
5. Restart the backend so it reloads `.env`.
6. Open the API docs and run `POST /api/ai/live-check` with:

```json
{
  "provider": "openai",
  "consent": true,
  "allow_local_fallback": false
}
```

Or use Terminal:

```bash
curl -sS -X POST http://127.0.0.1:8000/api/ai/live-check \
  -H 'Content-Type: application/json' \
  -d '{"provider":"openai","consent":true,"allow_local_fallback":false}'
```

Success returns `"ok": true`, `provider_used: "openai"`, `status:
"COMPLETED"`, the model, and small estimated/actual cost fields. A 400, 429,
502, or 503 response is a real failed/blocked check; do not describe it as a
successful live integration.

After the minimal check succeeds, select **OpenAI Responses API** in the UI,
read and check the disclosure, and run one workflow. Confirm the result is
labeled `openai`, refresh the page, and inspect `/api/ai/requests` to verify the
consent time, status, model, and usage record persisted. Raw prompts are not
stored.

## Configuration

| Variable | Default | Purpose |
|---|---:|---|
| `OPENAI_API_KEY` | blank | Enables server-side provider access; never commit it |
| `OPENAI_MODEL` | `gpt-5.6-luna` | Server-selected Responses API model |
| `OPENAI_TIMEOUT_SECONDS` | `30` | Per-request SDK timeout, bounded to 1–120 seconds |
| `OPENAI_MAX_RETRIES` | `2` | SDK retry count, bounded to 0–5 |
| `OPENAI_MAX_OUTPUT_TOKENS` | `2000` | Maximum structured output tokens |
| `OPENAI_MONTHLY_BUDGET_CENTS` | `0` | Local guard; zero disables live requests |
| `OPENAI_MONTHLY_REQUEST_LIMIT` | `20` | Maximum reserved live calls per UTC month |
| `OPENAI_INPUT_USD_PER_MILLION_TOKENS` | `0.20` | Input price used for local estimates |
| `OPENAI_OUTPUT_USD_PER_MILLION_TOKENS` | `1.20` | Output price used for local estimates |
| `DATABASE_URL` | local SQLite | Database connection |
| `MAX_UPLOAD_BYTES` | 5 MiB | Maximum PDF/DOCX size |
| `CORS_ORIGINS` | local Vite origins | Browsers allowed to call the backend |
| `VITE_API_URL` | blank | Optional deployed backend origin for the frontend |

The application budget is a conservative local safety guard, not a replacement
for project-level spend limits in the OpenAI Platform.

## Cancellation and restart behavior

- The browser creates the request ID before starting a provider call, so a
  cancellation action can be recorded independently.
- If an OpenAI HTTPS request is already in flight, cancellation may not prevent
  provider billing. The application discards a late result and saves no career
  artifact after the cancellation flag is observed.
- If the backend stops during a request, startup recovery changes `RUNNING` to
  `INTERRUPTED` with `INTERRUPTED_AFTER_RESTART`. It does not fabricate a result
  or pretend the request resumed.
- Start a fresh request after an interrupted run. Request IDs cannot be reused.

## API overview

| Method | Path | Description |
|---|---|---|
| POST | `/api/resumes/upload` | Parse and store a PDF/DOCX resume |
| POST | `/api/resumes/{id}/analyze` | Local-demo or consented OpenAI feedback |
| POST | `/api/jobs/{id}/match` | Local-demo or consented OpenAI comparison |
| POST | `/api/jobs/{id}/cover-letter` | Generate a validated draft |
| POST | `/api/jobs/{id}/skill-gap` | Generate validated skill-gap guidance |
| GET | `/api/ai/status` | Safe readiness and budget summary |
| GET | `/api/ai/requests` | Last 50 privacy-safe request records |
| POST | `/api/ai/requests/{request_id}/cancel` | Record cancellation for an active request |
| POST | `/api/ai/live-check` | Minimal, no-fallback live provider verification |
| CRUD | `/api/applications` | Manage application records |

## Verification

Backend:

```bash
cd backend
source .venv/bin/activate
python -m app.migrations
python -m pytest -q
python -m compileall -q app
python -m ruff check app tests
python -m ruff format --check app tests
```

Frontend:

```bash
cd frontend
npm ci
npm run lint
npm run build
npm audit --audit-level=high
```

The automated suite mocks the provider; it proves request construction,
Structured Output validation, safe errors, local flow, budgets, persistence,
cancellation flags, and restart reconciliation. It does not prove account
access, billing status, a successful live call, or model-response quality.

## Security and privacy boundaries

- API routes have no authentication and are intended for localhost only.
- Resume text and generated artifacts are stored unencrypted in SQLite.
- Resume/job text is sent to OpenAI only after the user selects OpenAI and
  confirms the disclosure for that request.
- Responses use `store=False`, which avoids Responses API application-state
  storage but does not by itself disable abuse-monitoring retention. Review the current official
  [OpenAI data controls](https://developers.openai.com/api/docs/guides/your-data)
  before using sensitive personal data.
- Structured Outputs follow the official
  [OpenAI structured-output guidance](https://developers.openai.com/api/docs/guides/structured-outputs).
- Do not deploy with real personal data until authentication, authorization,
  encrypted storage, retention/deletion controls, rate limiting, CSRF strategy,
  observability, backups, and production secret management are added.

## License

MIT. See [LICENSE](LICENSE).
