# AI Career Assistant

Full-stack portfolio project: upload a resume (PDF/DOCX), get AI feedback, compare against job descriptions, generate cover letters, analyze skill gaps, and track applications.

- **Frontend:** React (Vite) + TypeScript + Tailwind CSS v4  
- **Backend:** FastAPI + SQLAlchemy + SQLite  
- **AI:** OpenAI API (`gpt-4o-mini` by default) — key stays on the server  

## Architecture (how it works)

1. **Browser** loads the React SPA. In development, Vite **proxies** requests from `/api/*` to `http://127.0.0.1:8000`, so you avoid CORS issues and do not need to hardcode the API URL.
2. **FastAPI** exposes REST endpoints under `/api/...`. File uploads go to `POST /api/resumes/upload`; the backend extracts text with `pypdf` / `python-docx` and stores it in **SQLite**.
3. **AI features** call OpenAI from `app/services/ai_service.py` only. The frontend never sees your API key.
4. **Production:** build the frontend (`npm run build`) and serve static files from a host (e.g. Vercel/Netlify). Set `VITE_API_URL` to your public API URL, and deploy the FastAPI app (e.g. Railway, Render, Fly.io) with `OPENAI_API_KEY` and `CORS_ORIGINS` configured.

## Quick start

### 1. Backend

```bash
cd backend
cp .env.example .env
# Edit .env: set OPENAI_API_KEY=sk-...
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Or: `chmod +x run_dev.sh && ./run_dev.sh`

API docs: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

If `npm install` fails with cache permission errors on macOS, use a project-local cache:

```bash
npm install --cache "$(pwd)/.npm-cache"
```

### 3. Environment variables

| Location | Variable | Purpose |
|----------|----------|---------|
| `backend/.env` | `OPENAI_API_KEY` | Required for AI endpoints |
| `backend/.env` | `DATABASE_URL` | Optional; default SQLite file in `backend/` |
| `backend/.env` | `CORS_ORIGINS` | Comma-separated origins for production frontend |
| `frontend/.env` | `VITE_API_URL` | Production API base URL (omit in dev when using proxy) |

## API overview

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/resumes/upload` | Multipart file upload |
| GET | `/api/resumes` | List resumes |
| POST | `/api/resumes/{id}/analyze` | AI resume feedback |
| POST | `/api/jobs` | Create job posting |
| POST | `/api/jobs/{id}/match` | Resume vs job match score |
| POST | `/api/jobs/{id}/cover-letter` | Generate cover letter |
| POST | `/api/jobs/{id}/skill-gap` | Skill gap analysis |
| CRUD | `/api/applications` | Application tracker |
| GET | `/api/dashboard` | Dashboard stats |

## Deployment (outline)

- **Backend:** Container or PaaS running `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set env vars; use PostgreSQL by changing `DATABASE_URL` if you outgrow SQLite.
- **Frontend:** `npm run build`; deploy `frontend/dist`. Set `VITE_API_URL` to the public API origin before building.
- **Security:** Never expose `OPENAI_API_KEY` to the client; restrict CORS to your frontend domain.

## License

MIT — use freely for learning and portfolio use.
