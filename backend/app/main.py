"""
FastAPI entrypoint: CORS, database tables, and API routers.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import applications, dashboard, jobs, resumes


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create tables on startup (fine for SQLite demos; use Alembic for production PG)
    Base.metadata.create_all(bind=engine)
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


@app.get("/health")
def health():
    """Load balancer / uptime check."""
    return {"status": "ok"}
