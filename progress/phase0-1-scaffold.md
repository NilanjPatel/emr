# Phase 0.1 — Python FastAPI Scaffold

**Status:** Complete  
**Date:** 2026-06-29  
**Tests:** 9/9 passing

## What Was Built

```
oscar-next/backend/
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI app, lifespan, middleware wiring, router registration
│   ├── config.py        # Pydantic Settings from .env — typed, cached
│   ├── database.py      # Async SQLAlchemy engine + session factory
│   ├── middleware/
│   │   ├── audit.py     # PHIPA audit middleware → oscar_log table (GATE for all patient endpoints)
│   │   └── auth.py      # JWT RS256 validation stub (wired fully in Phase 0.4)
│   ├── models/          # Empty — SQLAlchemy models added per phase
│   └── routers/
│       ├── health.py        # GET /health, GET /health/db
│       └── admin_config.py  # GET/PATCH /admin/config (admin role only, masked secrets)
├── tests/
│   └── test_scaffold.py  # 9 tests — app, config, audit middleware
├── .env.example          # Template — never commit .env
├── .python-version       # 3.12
└── pyproject.toml        # uv project, all deps locked
```

## Key Decisions Made

- `uv` as package manager (confirmed by user)
- `.env` for config (confirmed by user) — NOT oscar.properties
- `pydantic-settings` reads `.env` into typed `Settings` class
- Async SQLAlchemy engine (`aiomysql` driver) — reflects existing schema, never alters it
- Audit middleware wired BEFORE auth middleware in stack — runs after auth, before route handlers
- `/admin/config` endpoint: secrets masked on read, restart required after write — confirmed approach

## Tests Verify

- `/health` endpoint responds 200
- `/docs` available in development mode
- OpenAPI schema has correct title
- `Settings` loads with correct defaults
- Database URL format is `mysql+aiomysql://...`
- Audit middleware skips `/health`, `/docs`, `/openapi.json`
- Audit middleware audits all `/fhir/R4/Patient*`, `/fhir/R4/Appointment*` etc.
- Audit path-to-table mapping correct (Patient→demographic, Appointment→appointment, etc.)
- Audit resource ID extraction from URL path

## Next Step

Phase 0.2 — SQLAlchemy + MariaDB connection (read-only verify against live Oscar DB)
- Connect to the actual running Oscar MariaDB
- Reflect `demographic`, `appointment`, `provider`, `casemgmt_note`, `oscar_log` tables
- Verify read works, write to `oscar_log` works
- Spot-check: `SELECT * FROM demographic LIMIT 5` returns real patient records
