"""
Phase 1 — Demographic audit coverage tests.

Verifies:
  1. All FHIR Patient paths are covered by AuditMiddleware
  2. _should_audit returns correct values for all Phase 1 paths
  3. Oscar-style paths /api/v1/patients/* are NOT auto-audited
     (they use explicit _write_oscar_audit calls instead)
  4. audit.py path-to-table mapping is correct for Patient resource
"""
import pytest
from app.middleware.audit import AuditMiddleware, AUDITED_PATH_PREFIXES


def _audit():
    return AuditMiddleware(app=None)


# ── FHIR Patient path coverage ────────────────────────────────────────────────

def test_patient_search_path_audited():
    assert _audit()._should_audit("/fhir/R4/Patient")


def test_patient_read_path_audited():
    assert _audit()._should_audit("/fhir/R4/Patient/1001")


def test_patient_everything_path_audited():
    assert _audit()._should_audit("/fhir/R4/Patient/1001/$everything")


def test_patient_update_path_audited():
    assert _audit()._should_audit("/fhir/R4/Patient/1001")


def test_fhir_patient_prefix_in_audited_prefixes():
    assert "/fhir/R4/Patient" in AUDITED_PATH_PREFIXES


# ── Path-to-table mapping ──────────────────────────────────────────────────────

def test_patient_maps_to_demographic():
    assert _audit()._path_to_table("/fhir/R4/Patient/123") == "demographic"


def test_patient_search_maps_to_demographic():
    assert _audit()._path_to_table("/fhir/R4/Patient") == "demographic"


# ── Resource ID extraction ─────────────────────────────────────────────────────

def test_resource_id_extracted_correctly():
    assert _audit()._extract_resource_id("/fhir/R4/Patient/1001") == "1001"


def test_resource_id_none_for_search():
    assert _audit()._extract_resource_id("/fhir/R4/Patient") is None


def test_resource_id_dollar_operation():
    # $everything — id is the patient id, not the operation name
    result = _audit()._extract_resource_id("/fhir/R4/Patient/1001/$everything")
    assert result == "1001"


# ── Oscar /api/v1/* paths NOT auto-audited ────────────────────────────────────

def test_oscar_search_not_auto_audited():
    assert not _audit()._should_audit("/api/v1/patients/search")


def test_oscar_get_not_auto_audited():
    assert not _audit()._should_audit("/api/v1/patients/1001")


def test_oscar_banner_not_auto_audited():
    assert not _audit()._should_audit("/api/v1/patients/1001/banner")


def test_oscar_ext_not_auto_audited():
    assert not _audit()._should_audit("/api/v1/patients/1001/ext")


def test_oscar_contacts_not_auto_audited():
    assert not _audit()._should_audit("/api/v1/patients/1001/contacts")


def test_oscar_consent_not_auto_audited():
    assert not _audit()._should_audit("/api/v1/patients/1001/consent")


def test_oscar_merge_not_auto_audited():
    assert not _audit()._should_audit("/api/v1/patients/1001/merge/999")


# ── Paths that must always be skipped ─────────────────────────────────────────

def test_health_skipped():
    assert not _audit()._should_audit("/health")


def test_docs_skipped():
    assert not _audit()._should_audit("/docs")


def test_openapi_skipped():
    assert not _audit()._should_audit("/openapi.json")


def test_redoc_skipped():
    assert not _audit()._should_audit("/redoc")


def test_admin_config_skipped():
    assert not _audit()._should_audit("/admin/config")


# ── Method-to-action mapping ───────────────────────────────────────────────────

def test_get_maps_to_read():
    assert _audit()._map_method_to_action("GET") == "read"


def test_post_maps_to_create():
    assert _audit()._map_method_to_action("POST") == "create"


def test_put_maps_to_update():
    assert _audit()._map_method_to_action("PUT") == "update"


def test_patch_maps_to_update():
    assert _audit()._map_method_to_action("PATCH") == "update"


def test_delete_maps_to_delete():
    assert _audit()._map_method_to_action("DELETE") == "delete"
