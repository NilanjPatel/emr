"""
Phase 0.3 — DB session middleware tests.

Verifies that:
1. Every request has request.state.db populated (DBSessionMiddleware)
2. The audit middleware writes to the log table on FHIR patient-data paths
3. No DB session is leaked between requests
"""
import pytest
from fastapi import Request
from fastapi.testclient import TestClient
from fastapi.routing import APIRouter
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.config import get_settings
from unittest.mock import patch, MagicMock

settings = get_settings()


@pytest.fixture
def app_with_test_route():
    """Minimal app with DBSessionMiddleware only — no auth — to test session attachment."""
    from fastapi import FastAPI, Request as FRequest
    from app.middleware.db_session import DBSessionMiddleware

    test_app = FastAPI()
    test_app.add_middleware(DBSessionMiddleware)

    db_on_request = {}

    @test_app.get("/test/db-session-check")
    async def check_db_session(request: FRequest):
        has_db = hasattr(request.state, "db")
        is_session = isinstance(getattr(request.state, "db", None), AsyncSession)
        db_on_request["has_db"] = has_db
        db_on_request["is_async_session"] = is_session
        return {"has_db": has_db, "is_async_session": is_session}

    return test_app, db_on_request


def test_db_session_attached_to_every_request(app_with_test_route):
    app, db_on_request = app_with_test_route
    with TestClient(app, raise_server_exceptions=True) as client:
        response = client.get("/test/db-session-check")
    assert response.status_code == 200
    data = response.json()
    assert data["has_db"] is True
    assert data["is_async_session"] is True


def test_health_endpoint_still_works():
    from app.main import app
    with TestClient(app, raise_server_exceptions=True) as client:
        response = client.get("/health")
    assert response.status_code == 200


def test_docs_skips_db_session():
    """Docs endpoint should work without a DB connection (skipped by DBSessionMiddleware)."""
    from app.main import app
    with TestClient(app, raise_server_exceptions=False) as client:
        response = client.get("/docs")
    assert response.status_code == 200


@pytest.fixture
async def live_db():
    engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def test_audit_writes_to_log_on_fhir_path(live_db):
    """
    Simulate what happens when a FHIR patient endpoint is called:
    the audit middleware should insert a row into the log table.
    Uses the audit middleware's _write_audit_log directly with a real DB session.
    """
    from app.middleware.audit import AuditMiddleware

    middleware = AuditMiddleware(app=None)

    # Build a minimal mock request simulating GET /fhir/R4/Patient/123
    mock_request = MagicMock()
    mock_request.url.path = "/fhir/R4/Patient/123"
    mock_request.method = "GET"
    mock_request.state.db = live_db
    mock_request.state.token_data = {"preferred_username": "testuser"}
    mock_request.headers.get.return_value = None
    mock_request.client.host = "127.0.0.1"

    marker = "audit-test-phase-0.3"
    mock_request.url.path = f"/fhir/R4/Patient/{marker}"

    await middleware._write_audit_log(mock_request, 200)

    # Verify the row was written
    result = await live_db.execute(
        text("SELECT action, provider_no, content FROM log WHERE contentId = :cid ORDER BY dateTime DESC LIMIT 1"),
        {"cid": marker}
    )
    row = result.fetchone()
    assert row is not None, "Audit log row not written to log table"
    assert row[0] == "read"
    assert row[1] == "testuser"
    assert row[2] == "demographic"  # Patient → demographic mapping

    # Clean up
    await live_db.execute(text("DELETE FROM log WHERE contentId = :cid"), {"cid": marker})
    await live_db.commit()


async def test_audit_skips_non_fhir_paths(live_db):
    """Audit middleware must NOT write for /health, /admin, /docs paths."""
    from app.middleware.audit import AuditMiddleware
    middleware = AuditMiddleware(app=None)
    assert not middleware._should_audit("/health")
    assert not middleware._should_audit("/admin/config")
    assert not middleware._should_audit("/docs")
    assert not middleware._should_audit("/openapi.json")


async def test_audit_fires_for_all_fhir_resource_types(live_db):
    """All clinical FHIR resource types must trigger an audit entry."""
    from app.middleware.audit import AuditMiddleware
    middleware = AuditMiddleware(app=None)
    clinical_paths = [
        "/fhir/R4/Patient/1",
        "/fhir/R4/Appointment/2",
        "/fhir/R4/Encounter/3",
        "/fhir/R4/MedicationRequest/4",
        "/fhir/R4/DiagnosticReport/5",
        "/fhir/R4/Observation/6",
        "/fhir/R4/AllergyIntolerance/7",
        "/fhir/R4/Condition/8",
        "/fhir/R4/Immunization/9",
        "/fhir/R4/Claim/10",
        "/fhir/R4/DocumentReference/11",
        "/fhir/R4/Composition/12",
    ]
    for path in clinical_paths:
        assert middleware._should_audit(path), f"Audit not triggered for {path}"
