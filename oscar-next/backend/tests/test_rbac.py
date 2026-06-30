"""
Phase 0.6 — RBAC middleware and privilege matrix tests.

Covers:
- Privilege matrix loads correctly from Oscar DB
- Privilege ordering (r < u < x < o)
- Role → object → privilege resolution
- FHIR path → Oscar object mapping
- require_permission() dependency enforces access
- request.state.can() helper works correctly
"""
import pytest
from fastapi import FastAPI, Request, Depends
from fastapi.testclient import TestClient
from sqlalchemy import text

from app.middleware.rbac import (
    RBACMiddleware,
    load_privilege_matrix,
    require_permission,
    _get_privilege_matrix,
    _invalidate_privilege_cache,
    _privilege_gte,
    _roles_have_privilege,
    _resolve_oscar_object,
    FHIR_PATH_TO_OSCAR_OBJECT,
)
from app.config import get_settings

settings = get_settings()


# ── Privilege ordering ────────────────────────────────────────────────────────

def test_privilege_gte_read_satisfies_read():
    assert _privilege_gte("r", "r") is True

def test_privilege_gte_update_satisfies_read():
    assert _privilege_gte("u", "r") is True

def test_privilege_gte_execute_satisfies_update():
    assert _privilege_gte("x", "u") is True

def test_privilege_gte_read_does_not_satisfy_update():
    assert _privilege_gte("r", "u") is False

def test_privilege_gte_read_does_not_satisfy_execute():
    assert _privilege_gte("r", "x") is False

def test_privilege_gte_owner_satisfies_all():
    for level in ["r", "u", "x", "o"]:
        assert _privilege_gte("o", level) is True


# ── Privilege matrix logic ────────────────────────────────────────────────────

def test_roles_have_privilege_with_mock_matrix(monkeypatch):
    """_roles_have_privilege must use the cached matrix correctly."""
    mock_matrix = {
        "doctor":       {"_demographic": "x", "_rx": "x", "_billing": "x"},
        "nurse":        {"_demographic": "x", "_appointment": "x"},
        "receptionist": {"_demographic": "r", "_appointment": "x"},
    }
    monkeypatch.setattr("app.middleware.rbac._privilege_matrix", mock_matrix)

    assert _roles_have_privilege(["doctor"], "_demographic", "r") is True
    assert _roles_have_privilege(["doctor"], "_demographic", "x") is True
    assert _roles_have_privilege(["nurse"], "_rx", "r") is False
    assert _roles_have_privilege(["receptionist"], "_demographic", "u") is False
    assert _roles_have_privilege(["receptionist"], "_demographic", "r") is True
    # Multiple roles: nurse has no _rx, doctor does
    assert _roles_have_privilege(["nurse", "doctor"], "_rx", "r") is True


def test_empty_roles_denied(monkeypatch):
    mock_matrix = {"doctor": {"_demographic": "x"}}
    monkeypatch.setattr("app.middleware.rbac._privilege_matrix", mock_matrix)
    assert _roles_have_privilege([], "_demographic", "r") is False


def test_unknown_role_denied(monkeypatch):
    mock_matrix = {"doctor": {"_demographic": "x"}}
    monkeypatch.setattr("app.middleware.rbac._privilege_matrix", mock_matrix)
    assert _roles_have_privilege(["unknown_role"], "_demographic", "r") is False


# ── FHIR path → Oscar object mapping ─────────────────────────────────────────

def make_mock_request(path: str, method: str = "GET") -> Request:
    from starlette.requests import Request as StarletteRequest
    scope = {
        "type": "http",
        "method": method,
        "path": path,
        "query_string": b"",
        "headers": [],
    }
    return StarletteRequest(scope)


def test_patient_path_maps_to_demographic():
    req = make_mock_request("/fhir/R4/Patient/123")
    assert _resolve_oscar_object(req) == "_demographic"

def test_appointment_path_maps_to_appointment():
    req = make_mock_request("/fhir/R4/Appointment")
    assert _resolve_oscar_object(req) == "_appointment"

def test_medication_path_maps_to_rx():
    req = make_mock_request("/fhir/R4/MedicationRequest/456")
    assert _resolve_oscar_object(req) == "_rx"

def test_diagnostic_report_maps_to_lab():
    req = make_mock_request("/fhir/R4/DiagnosticReport")
    assert _resolve_oscar_object(req) == "_lab"

def test_claim_maps_to_billing():
    req = make_mock_request("/fhir/R4/Claim")
    assert _resolve_oscar_object(req) == "_billing"

def test_unknown_fhir_path_returns_none():
    req = make_mock_request("/fhir/R4/UnknownResource")
    assert _resolve_oscar_object(req) is None

def test_non_fhir_path_returns_none():
    req = make_mock_request("/health")
    assert _resolve_oscar_object(req) is None

def test_all_mapped_fhir_paths_resolve():
    """Every entry in the mapping table must produce a non-None object."""
    for prefix in FHIR_PATH_TO_OSCAR_OBJECT:
        req = make_mock_request(f"{prefix}/1")
        result = _resolve_oscar_object(req)
        assert result is not None, f"{prefix} resolved to None"


# ── require_permission dependency ─────────────────────────────────────────────

def make_rbac_test_app(roles: list[str], monkeypatch) -> FastAPI:
    """Build a minimal app that injects roles and tests require_permission."""
    mock_matrix = {
        "doctor":       {"_demographic": "x", "_rx": "x"},
        "receptionist": {"_demographic": "r"},
    }
    monkeypatch.setattr("app.middleware.rbac._privilege_matrix", mock_matrix)

    app = FastAPI()
    app.add_middleware(RBACMiddleware)

    # Inject roles via a custom middleware (simulates AuthMiddleware output)
    from starlette.middleware.base import BaseHTTPMiddleware
    class InjectRolesMiddleware(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.state.roles = roles
            return await call_next(request)

    app.add_middleware(InjectRolesMiddleware)

    @app.get(
        "/fhir/R4/Patient",
        dependencies=[require_permission("_demographic", "r")],
    )
    def get_patients():
        return {"ok": True}

    @app.get(
        "/fhir/R4/MedicationRequest",
        dependencies=[require_permission("_rx", "x")],
    )
    def get_rx():
        return {"ok": True}

    return app


def test_doctor_can_read_demographic(monkeypatch):
    app = make_rbac_test_app(["doctor"], monkeypatch)
    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/fhir/R4/Patient").status_code == 200


def test_receptionist_read_only_on_demographic(monkeypatch):
    app = make_rbac_test_app(["receptionist"], monkeypatch)
    client = TestClient(app, raise_server_exceptions=False)
    # Receptionist has "r" on _demographic — read is allowed
    assert client.get("/fhir/R4/Patient").status_code == 200


def test_receptionist_blocked_from_rx(monkeypatch):
    app = make_rbac_test_app(["receptionist"], monkeypatch)
    client = TestClient(app, raise_server_exceptions=False)
    # Receptionist has no _rx privileges
    assert client.get("/fhir/R4/MedicationRequest").status_code == 403


def test_no_roles_blocked(monkeypatch):
    app = make_rbac_test_app([], monkeypatch)
    client = TestClient(app, raise_server_exceptions=False)
    assert client.get("/fhir/R4/Patient").status_code == 403


# ── Live DB: matrix loads from Oscar secObjPrivilege ─────────────────────────

@pytest.fixture
async def live_db():
    from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
    engine = create_async_engine(settings.database_url, echo=False)
    factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def test_load_privilege_matrix_from_live_db(live_db):
    """load_privilege_matrix must populate cache from real Oscar DB."""
    _invalidate_privilege_cache()
    await load_privilege_matrix(live_db)
    matrix = _get_privilege_matrix()

    assert len(matrix) > 0, "Privilege matrix is empty"
    assert "doctor" in matrix, "Expected 'doctor' role in privilege matrix"
    assert "_demographic" in matrix["doctor"], "Doctor must have _demographic privilege"


async def test_doctor_has_demographic_access_in_live_db(live_db):
    """doctor role must have at least read access to _demographic in real DB."""
    _invalidate_privilege_cache()
    await load_privilege_matrix(live_db)
    assert _roles_have_privilege(["doctor"], "_demographic", "r") is True


async def test_nurse_has_appointment_access_in_live_db(live_db):
    """nurse role must have at least read access to _appointment in real DB."""
    _invalidate_privilege_cache()
    await load_privilege_matrix(live_db)
    assert _roles_have_privilege(["nurse"], "_appointment", "r") is True
