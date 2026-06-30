"""
Oscar-AI sidecar — FastAPI application.

Two-tier AI strategy:
  Ollama (on-premise) — real-time PHI-safe tasks (encounter assist, CDS)
  Anthropic Claude  — async de-identified tasks (summarization, billing codes)

All AI output is suggestion-only. Nothing is auto-saved.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.routers import billing, cds, encounter, summarize
from app.services import ollama_client


@asynccontextmanager
async def lifespan(application: FastAPI):
    settings = get_settings()
    ollama_up = await ollama_client.is_available()
    application.state.ollama_available = ollama_up
    application.state.anthropic_available = settings.anthropic_available
    yield


settings = get_settings()

app = FastAPI(
    title="Oscar-AI Sidecar",
    version="0.1.0",
    description="AI assistance layer for Oscar EMR — suggestion-only, PIPEDA/PHIPA compliant",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(encounter.router)
app.include_router(summarize.router)
app.include_router(cds.router)
app.include_router(billing.router)


@app.get("/health")
async def health():
    ollama_up = await ollama_client.is_available()
    return {
        "status": "ok",
        "ollama": "available" if ollama_up else "unavailable",
        "anthropic": "configured" if settings.anthropic_available else "not configured",
        "suggestion_only": settings.suggestion_only,
    }
