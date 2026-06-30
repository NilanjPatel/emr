"""
Phase 0.1 scaffold tests — verify the app starts, config loads, and routes exist.
Does NOT require a live database connection.
"""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock


@pytest.fixture
def client():
    # Patch DB engine so tests run without a live MariaDB
    with patch("app.database.create_async_engine"):
        from app.main import app
        with TestClient(app, raise_server_exceptions=False) as c:
            yield c


def test_health_endpoint(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "oscar-next-api"


def test_docs_available_in_development(client):
    response = client.get("/docs")
    assert response.status_code == 200


def test_openapi_schema_exists(client):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    assert schema["info"]["title"] == "Oscar-Next FHIR R4 API"


def test_config_loads():
    from app.config import get_settings
    settings = get_settings()
    assert settings.app_port == 8000
    assert settings.fhir_base_url.endswith("/fhir/R4")


def test_database_url_format():
    from app.config import get_settings
    settings = get_settings()
    url = settings.database_url
    assert url.startswith("mysql+aiomysql://")
    assert "oscar" in url


def test_audit_middleware_skips_health():
    from app.middleware.audit import AuditMiddleware
    middleware = AuditMiddleware(app=None)
    assert not middleware._should_audit("/health")
    assert not middleware._should_audit("/docs")
    assert not middleware._should_audit("/openapi.json")


def test_audit_middleware_audits_fhir_paths():
    from app.middleware.audit import AuditMiddleware
    middleware = AuditMiddleware(app=None)
    assert middleware._should_audit("/fhir/R4/Patient")
    assert middleware._should_audit("/fhir/R4/Patient/12345")
    assert middleware._should_audit("/fhir/R4/Appointment")
    assert middleware._should_audit("/fhir/R4/MedicationRequest/99")


def test_audit_path_to_table_mapping():
    from app.middleware.audit import AuditMiddleware
    middleware = AuditMiddleware(app=None)
    assert middleware._path_to_table("/fhir/R4/Patient/123") == "demographic"
    assert middleware._path_to_table("/fhir/R4/Appointment/5") == "appointment"
    assert middleware._path_to_table("/fhir/R4/MedicationRequest/7") == "prescription"


def test_audit_resource_id_extraction():
    from app.middleware.audit import AuditMiddleware
    middleware = AuditMiddleware(app=None)
    assert middleware._extract_resource_id("/fhir/R4/Patient/12345") == "12345"
    assert middleware._extract_resource_id("/fhir/R4/Patient") is None
