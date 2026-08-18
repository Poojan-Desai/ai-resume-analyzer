"""
FastAPI entrypoint: CORS, database tables, and API routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import SessionLocal, engine
from app.migrations import run_migrations
from app.routers import ai, applications, dashboard, jobs, resumes
from app.services import ai_service, ai_usage


@asynccontextmanager
async def lifespan(app: FastAPI):
    run_migrations(engine)
    with SessionLocal() as db:
        ai_usage.reconcile_interrupted_requests(db)
    yield


app = FastAPI(
    title="AI Career Assistant API",
    description="Resume analysis, job matching, cover letters, and application tracking.",
    version="1.0.0",
    lifespan=lifespan,
)

# Allow the Vite dev server (and production frontend URL) to call the API
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(resumes.router, prefix="/api")
app.include_router(jobs.router, prefix="/api")
app.include_router(applications.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(ai.router, prefix="/api")


@app.get("/health")
def health():
    """Load balancer / uptime check."""
    return {"status": "ok", "ai": ai_service.service_status()}
