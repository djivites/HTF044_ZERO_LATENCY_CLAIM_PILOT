"""
ClaimPilot — FastAPI Backend
Entry point: uvicorn backend.main:app --reload
"""
import logging
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import cases, documents, analysis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ClaimPilot API",
    description=(
        "Zero-latency AI-powered dispute evidence analysis. "
        "Upload documents, extract evidence, detect contradictions, and generate dispute letters."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS (allow the Vite dev server on :3000 / :5173) ───────────────────────
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:5173",
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ─────────────────────────────────────────────────────────────────
app.include_router(documents.router, prefix="/api/v1/documents", tags=["Documents"])
app.include_router(cases.router,     prefix="/api/v1/cases",     tags=["Cases"])
app.include_router(analysis.router,  prefix="/api/v1/analysis",  tags=["Analysis"])


# ─── Health check ─────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
def health():
    return {"status": "ok", "service": "ClaimPilot API"}


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "Welcome to ClaimPilot API",
        "docs": "/docs",
        "health": "/health",
    }
