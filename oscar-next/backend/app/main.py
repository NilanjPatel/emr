from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import get_settings
from app.database import engine
from app.middleware.db_session import DBSessionMiddleware
from app.middleware.audit import AuditMiddleware
from app.middleware.auth import AuthMiddleware
from app.middleware.rbac import RBACMiddleware, load_privilege_matrix
from app.database import AsyncSessionLocal
from app.routers import health, admin_config, demographic

settings = get_settings()
logging.basicConfig(level=settings.log_level)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Oscar-Next API starting — env=%s", settings.app_env)
    logger.info("Database: %s@%s:%s/%s", settings.db_user, settings.db_host, settings.db_port, settings.db_name)
    async with AsyncSessionLocal() as db:
        await load_privilege_matrix(db)
    yield
    logger.info("Oscar-Next API shutting down")
    await engine.dispose()


app = FastAPI(
    title="Oscar-Next FHIR R4 API",
    version="0.1.0",
    description="Modern FHIR R4 backend for Oscar EMR migration",
    lifespan=lifespan,
    # Disable docs in production
    docs_url="/docs" if settings.is_development else None,
    redoc_url="/redoc" if settings.is_development else None,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware execution order (Starlette adds in reverse — last added runs first):
# Request:  DBSession → Audit → Auth → route handler
# Response: route handler → Auth → Audit → DBSession
# Middleware execution order (Starlette adds in reverse — last added runs first on request):
# Request:  DBSession → Audit → Auth → RBAC → route handler
app.add_middleware(RBACMiddleware)
app.add_middleware(AuditMiddleware)
app.add_middleware(DBSessionMiddleware)
app.add_middleware(
    AuthMiddleware,
    jwks_url=settings.jwks_url,
    issuer=settings.keycloak_issuer,
    audience=settings.keycloak_client_id,
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(health.router)

if settings.admin_config_enabled:
    app.include_router(admin_config.router)

# Phase 1 — Demographics (FHIR + Oscar-style endpoints in same router)
app.include_router(demographic.router)
