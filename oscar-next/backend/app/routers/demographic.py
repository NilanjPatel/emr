"""
Demographics router — Phase 1.

Exposes both FHIR R4 Patient endpoints and Oscar-style convenience endpoints.

FHIR R4 paths (/fhir/R4/Patient*):
  - Audit fires automatically via AuditMiddleware
  - RBAC enforced via require_permission("_demographic", ...)

Oscar-style paths (/api/v1/patients*):
  - Same RBAC, but no automatic audit → explicit audit_log call in each handler

PHIPA gate: sin is NEVER returned by any endpoint.
"""
from __future__ import annotations

import logging
from datetime import datetime, date
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.middleware.rbac import require_permission
from app.models.demographic import Demographic
from app.schemas.demographic import (
    ConsentCreate, ConsentResponse,
    DemographicContactCreate, DemographicContactResponse,
    DemographicCreate, DemographicResponse, DemographicUpdate,
    DuplicateCheckResponse, ExtFieldResponse,
    MergeHistoryResponse, MergeRequest,
    PatientBannerResponse, PatientSearchResponse, PatientSearchResult,
    ContactResponse, demographic_to_fhir_patient, PATIENT_STATUS_LABELS,
)
from app.services import demographic_service
from app.config import get_settings

logger = logging.getLogger(__name__)
router = APIRouter(tags=["Demographics"])
settings = get_settings()


# ── Shared helpers ────────────────────────────────────────────────────────────

def _get_provider_no(request: Request) -> str:
    token = getattr(request.state, "token_data", {}) or {}
    return token.get("preferred_username") or token.get("sub") or "unknown"


async def _write_oscar_audit(
    db: AsyncSession,
    request: Request,
    content: str,
    content_id: str,
    action: str,
) -> None:
    """Explicit audit for non-FHIR paths (AuditMiddleware doesn't cover /api/v1/*)."""
    try:
        await db.execute(
            text("""
                INSERT INTO log (dateTime, provider_no, action, content, contentId, ip, data)
                VALUES (:dt, :pno, :action, :content, :cid, :ip, :data)
            """),
            {
                "dt": datetime.now(),
                "pno": _get_provider_no(request),
                "action": action,
                "content": content,
                "cid": content_id,
                "ip": (request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
                       or (request.client.host if request.client else "unknown")),
                "data": f"{request.method} {request.url.path}",
            },
        )
    except Exception as exc:
        logger.error("Audit write failed for %s: %s", request.url.path, exc)


def _fhir_not_found(resource_type: str, resource_id: Any) -> dict:
    return {
        "resourceType": "OperationOutcome",
        "issue": [{
            "severity": "error",
            "code": "not-found",
            "diagnostics": f"{resource_type}/{resource_id} not found",
        }],
    }


def _patient_to_search_result(p: Demographic) -> PatientSearchResult:
    return PatientSearchResult(
        demographic_no=p.demographic_no,
        first_name=p.first_name,
        last_name=p.last_name,
        pref_name=p.pref_name,
        dob_iso=p.dob_iso,
        age=p.age,
        hin=p.hin,
        chart_no=p.chart_no,
        patient_status=p.patient_status,
        patient_status_label=PATIENT_STATUS_LABELS.get(p.patient_status or ""),
        provider_no=p.provider_no,
    )


# ══════════════════════════════════════════════════════════════════════════════
# FHIR R4 endpoints — audit automatic, RBAC via require_permission
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/fhir/R4/metadata", response_model=None)
async def fhir_capability_statement(request: Request):
    """CapabilityStatement — unauthenticated, SMART on FHIR conformance declaration."""
    base = settings.fhir_base_url
    return {
        "resourceType": "CapabilityStatement",
        "status": "active",
        "fhirVersion": "4.0.1",
        "format": ["application/fhir+json"],
        "rest": [{
            "mode": "server",
            "security": {
                "extension": [{
                    "url": "http://fhir-registry.smarthealthit.org/StructureDefinition/capabilities",
                    "extension": [
                        {"url": "authorize", "valueUri": f"https://auth.mapleclinics.ca/realms/oscar/protocol/openid-connect/auth"},
                        {"url": "token", "valueUri": f"https://auth.mapleclinics.ca/realms/oscar/protocol/openid-connect/token"},
                    ],
                }],
                "cors": True,
                "service": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/restful-security-service", "code": "SMART-on-FHIR"}]}],
            },
            "resource": [
                {
                    "type": "Patient",
                    "interaction": [
                        {"code": "read"}, {"code": "search-type"}, {"code": "update"},
                    ],
                    "searchParam": [
                        {"name": "family", "type": "string"},
                        {"name": "given", "type": "string"},
                        {"name": "birthdate", "type": "date"},
                        {"name": "identifier", "type": "token"},
                        {"name": "active", "type": "token"},
                    ],
                },
            ],
        }],
    }


@router.get(
    "/fhir/R4/Patient",
    response_model=None,
    dependencies=[require_permission("_demographic", "r")],
)
async def fhir_search_patients(
    request: Request,
    family: Optional[str] = Query(None),
    given: Optional[str] = Query(None),
    birthdate: Optional[str] = Query(None),
    identifier: Optional[str] = Query(None),
    active: Optional[str] = Query(None),
    _count: int = Query(20, alias="_count"),
    db: AsyncSession = Depends(get_db),
):
    """FHIR R4 Patient search — returns Bundle."""
    hin = ""
    chart_no = ""
    if identifier:
        # FHIR identifier: system|value or just value
        parts = identifier.split("|")
        val = parts[-1]
        if len(val) >= 9:
            hin = val
        else:
            chart_no = val

    # Parse DOB from FHIR birthdate (YYYY-MM-DD)
    year_of_birth = month_of_birth = date_of_birth_str = ""
    if birthdate:
        dob_parts = birthdate.split("-")
        if len(dob_parts) == 3:
            year_of_birth, month_of_birth, date_of_birth_str = dob_parts

    q = " ".join(filter(None, [given, family]))
    include_inactive = active == "false"

    total, patients = await demographic_service.search(
        db=db,
        q=q,
        hin=hin,
        chart_no=chart_no,
        include_inactive=include_inactive,
        limit=min(_count, 100),
        page=1,
    )

    base = settings.fhir_base_url
    entries = [
        {"fullUrl": f"{base}/Patient/{p.demographic_no}",
         "resource": demographic_to_fhir_patient(p, base)}
        for p in patients
    ]
    return {
        "resourceType": "Bundle",
        "type": "searchset",
        "total": total,
        "entry": entries,
    }


@router.get(
    "/fhir/R4/Patient/{demographic_no}",
    response_model=None,
    dependencies=[require_permission("_demographic", "r")],
)
async def fhir_read_patient(
    demographic_no: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """FHIR R4 Patient read."""
    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail=_fhir_not_found("Patient", demographic_no))
    return demographic_to_fhir_patient(patient, settings.fhir_base_url)


@router.put(
    "/fhir/R4/Patient/{demographic_no}",
    response_model=None,
    dependencies=[require_permission("_demographic", "u")],
)
async def fhir_update_patient(
    demographic_no: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """FHIR R4 Patient update — accepts FHIR Patient resource, maps to demographic table."""
    body = await request.json()
    provider_no = _get_provider_no(request)

    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail=_fhir_not_found("Patient", demographic_no))

    # Map FHIR fields back to Oscar demographic columns (best-effort)
    update = DemographicUpdate()
    names = body.get("name", [])
    official = next((n for n in names if n.get("use") == "official"), names[0] if names else None)
    if official:
        update.last_name = official.get("family")
        given_list = official.get("given", [])
        if given_list:
            update.first_name = given_list[0]
        if len(given_list) > 1:
            update.middle_names = " ".join(given_list[1:])
    nickname = next((n for n in names if n.get("use") == "nickname"), None)
    if nickname:
        update.pref_name = nickname.get("text")

    gender_map = {"male": "M", "female": "F", "other": "O", "unknown": "U"}
    if body.get("gender"):
        update.sex = gender_map.get(body["gender"], "U")

    if body.get("birthDate"):
        parts = body["birthDate"].split("-")
        if len(parts) == 3:
            update.year_of_birth, update.month_of_birth, update.date_of_birth = parts

    telecoms = body.get("telecom", [])
    for t in telecoms:
        if t.get("system") == "phone" and t.get("use") == "home":
            update.phone = t.get("value")
        elif t.get("system") == "phone" and t.get("use") == "mobile":
            update.phone2 = t.get("value")
        elif t.get("system") == "email":
            update.email = t.get("value")

    addresses = body.get("address", [])
    postal_addr = next((a for a in addresses if a.get("type") == "postal"), addresses[0] if addresses else None)
    if postal_addr:
        lines = postal_addr.get("line", [])
        update.address = lines[0] if lines else None
        update.city = postal_addr.get("city")
        update.province = postal_addr.get("state")
        update.postal = postal_addr.get("postalCode")

    updated = await demographic_service.update_patient(db, demographic_no, update, provider_no)
    return demographic_to_fhir_patient(updated, settings.fhir_base_url)


@router.get(
    "/fhir/R4/Patient/{demographic_no}/$everything",
    response_model=None,
    dependencies=[require_permission("_demographic", "r")],
)
async def fhir_patient_everything(
    demographic_no: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """FHIR $everything — Patient resource bundle with related resources stub."""
    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail=_fhir_not_found("Patient", demographic_no))

    base = settings.fhir_base_url
    entries = [{"fullUrl": f"{base}/Patient/{demographic_no}",
                "resource": demographic_to_fhir_patient(patient, base)}]

    return {
        "resourceType": "Bundle",
        "type": "collection",
        "entry": entries,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Oscar-style API endpoints — manual audit required
# ══════════════════════════════════════════════════════════════════════════════

@router.get(
    "/api/v1/patients/search",
    response_model=PatientSearchResponse,
    dependencies=[require_permission("_demographic", "r")],
)
async def search_patients(
    request: Request,
    q: str = Query("", description="Name / alias / preferred name search"),
    hin: str = Query("", description="Health card number (exact)"),
    chart_no: str = Query("", description="Chart number (exact)"),
    phone: str = Query(""),
    email: str = Query(""),
    include_inactive: bool = Query(False),
    limit: int = Query(20, ge=1, le=100),
    page: int = Query(1, ge=1),
    db: AsyncSession = Depends(get_db),
):
    await _write_oscar_audit(db, request, "demographic", "search", "read")

    total, patients = await demographic_service.search(
        db=db, q=q, hin=hin, chart_no=chart_no,
        phone=phone, email=email,
        include_inactive=include_inactive,
        limit=limit, page=page,
    )
    return PatientSearchResponse(
        total=total,
        page=page,
        limit=limit,
        results=[_patient_to_search_result(p) for p in patients],
    )


@router.get(
    "/api/v1/patients/{demographic_no}",
    response_model=DemographicResponse,
    dependencies=[require_permission("_demographic", "r")],
)
async def get_patient(
    demographic_no: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    await _write_oscar_audit(db, request, "demographic", str(demographic_no), "read")
    return DemographicResponse.from_orm_with_computed(patient)


@router.get(
    "/api/v1/patients/{demographic_no}/banner",
    response_model=PatientBannerResponse,
    dependencies=[require_permission("_demographic", "r")],
)
async def get_patient_banner(
    demographic_no: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    banner = await demographic_service.get_banner_data(db, demographic_no)
    if not banner:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    await _write_oscar_audit(db, request, "demographic", str(demographic_no), "read")
    return PatientBannerResponse(**banner)


@router.post(
    "/api/v1/patients",
    response_model=DemographicResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_permission("_demographic", "u")],
)
async def create_patient(
    data: DemographicCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    provider_no = _get_provider_no(request)
    patient = await demographic_service.create_patient(db, data, provider_no)
    await _write_oscar_audit(db, request, "demographic", str(patient.demographic_no), "create")
    return DemographicResponse.from_orm_with_computed(patient)


@router.put(
    "/api/v1/patients/{demographic_no}",
    response_model=DemographicResponse,
    dependencies=[require_permission("_demographic", "u")],
)
async def full_update_patient(
    demographic_no: int,
    data: DemographicUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    provider_no = _get_provider_no(request)
    patient = await demographic_service.update_patient(db, demographic_no, data, provider_no)
    if not patient:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    await _write_oscar_audit(db, request, "demographic", str(demographic_no), "update")
    return DemographicResponse.from_orm_with_computed(patient)


@router.patch(
    "/api/v1/patients/{demographic_no}",
    response_model=DemographicResponse,
    dependencies=[require_permission("_demographic", "u")],
)
async def partial_update_patient(
    demographic_no: int,
    data: DemographicUpdate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    provider_no = _get_provider_no(request)
    patient = await demographic_service.update_patient(db, demographic_no, data, provider_no)
    if not patient:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    await _write_oscar_audit(db, request, "demographic", str(demographic_no), "update")
    return DemographicResponse.from_orm_with_computed(patient)


@router.get(
    "/api/v1/patients/{demographic_no}/ext",
    dependencies=[require_permission("_demographic", "r")],
)
async def get_patient_ext(
    demographic_no: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    ext_fields = await demographic_service.get_ext_fields(db, demographic_no)
    await _write_oscar_audit(db, request, "demographicExt", str(demographic_no), "read")
    return [ExtFieldResponse.model_validate(e) for e in ext_fields]


@router.put(
    "/api/v1/patients/{demographic_no}/ext/{key_val}",
    dependencies=[require_permission("_demographic", "u")],
)
async def update_patient_ext(
    demographic_no: int,
    key_val: str,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    body = await request.json()
    value = body.get("value", "")
    provider_no = _get_provider_no(request)
    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    await demographic_service.upsert_ext_field(db, demographic_no, key_val, value, provider_no)
    await _write_oscar_audit(db, request, "demographicExt", str(demographic_no), "update")
    return {"key_val": key_val, "value": value}


@router.get(
    "/api/v1/patients/{demographic_no}/contacts",
    dependencies=[require_permission("_demographic", "r")],
)
async def get_patient_contacts(
    demographic_no: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    contacts = await demographic_service.get_contacts(db, demographic_no)
    await _write_oscar_audit(db, request, "DemographicContact", str(demographic_no), "read")
    results = []
    for dc, contact in contacts:
        dc_resp = DemographicContactResponse.model_validate(dc)
        if contact:
            dc_resp.contact = ContactResponse.model_validate(contact)
        results.append(dc_resp)
    return results


@router.post(
    "/api/v1/patients/{demographic_no}/contacts",
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_permission("_demographic", "u")],
)
async def add_patient_contact(
    demographic_no: int,
    data: DemographicContactCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    provider_no = _get_provider_no(request)
    dc = await demographic_service.add_contact(
        db, demographic_no, data.contactId, data.role, data.sdm, data.ec,
        data.mrp, data.health_care_team, data.best_contact,
        data.category, data.note, provider_no,
    )
    await _write_oscar_audit(db, request, "DemographicContact", str(demographic_no), "create")
    return DemographicContactResponse.model_validate(dc)


@router.delete(
    "/api/v1/patients/{demographic_no}/contacts/{contact_link_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[require_permission("_demographic", "u")],
)
async def delete_patient_contact(
    demographic_no: int,
    contact_link_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    deleted = await demographic_service.soft_delete_contact(db, contact_link_id, demographic_no)
    if not deleted:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": "Contact link not found"})
    await _write_oscar_audit(db, request, "DemographicContact", str(demographic_no), "delete")


@router.get(
    "/api/v1/patients/{demographic_no}/consent",
    dependencies=[require_permission("_demographic", "r")],
)
async def get_patient_consent(
    demographic_no: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    consents = await demographic_service.get_consents(db, demographic_no)
    await _write_oscar_audit(db, request, "Consent", str(demographic_no), "read")
    return [ConsentResponse.model_validate(c) for c in consents]


@router.post(
    "/api/v1/patients/{demographic_no}/consent",
    status_code=status.HTTP_201_CREATED,
    dependencies=[require_permission("_demographic", "u")],
)
async def add_patient_consent(
    demographic_no: int,
    data: ConsentCreate,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    provider_no = _get_provider_no(request)
    consent = await demographic_service.add_consent(
        db, demographic_no, data.consent_type_id, data.explicit, data.optout, provider_no
    )
    await _write_oscar_audit(db, request, "Consent", str(demographic_no), "create")
    return ConsentResponse.model_validate(consent)


@router.get(
    "/api/v1/patients/{demographic_no}/merge-history",
    dependencies=[require_permission("_demographic", "r")],
)
async def get_merge_history(
    demographic_no: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    history = await demographic_service.get_merge_history(db, demographic_no)
    await _write_oscar_audit(db, request, "demographic_merged", str(demographic_no), "read")
    return [MergeHistoryResponse.model_validate(h) for h in history]


@router.get(
    "/api/v1/patients/{demographic_no}/duplicates",
    response_model=DuplicateCheckResponse,
    dependencies=[require_permission("_demographic", "r")],
)
async def check_duplicates(
    demographic_no: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Check for potential duplicates of an existing patient."""
    patient = await demographic_service.get_by_id(db, demographic_no)
    if not patient:
        raise HTTPException(status_code=404, detail={"error": "not_found", "message": f"Patient {demographic_no} not found"})
    candidates = await demographic_service.score_duplicates(
        db=db,
        first_name=patient.first_name,
        last_name=patient.last_name,
        hin=patient.hin,
        year_of_birth=patient.year_of_birth,
        month_of_birth=patient.month_of_birth,
        date_of_birth=patient.date_of_birth,
        exclude_no=demographic_no,
    )
    await _write_oscar_audit(db, request, "demographic", str(demographic_no), "read")
    return DuplicateCheckResponse(has_duplicates=len(candidates) > 0, candidates=candidates)


@router.post(
    "/api/v1/patients/{demographic_no}/merge/{absorbed_no}",
    dependencies=[require_permission("_demographic", "u")],
)
async def merge_patients(
    demographic_no: int,
    absorbed_no: int,
    data: MergeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Merge absorbed_no into surviving demographic_no."""
    if demographic_no == absorbed_no:
        raise HTTPException(status_code=400, detail={"error": "invalid", "message": "Cannot merge a patient into themselves"})
    provider_no = _get_provider_no(request)
    success, error_msg = await demographic_service.merge_patients(db, demographic_no, absorbed_no, provider_no)
    if not success:
        raise HTTPException(status_code=409, detail={"error": "merge_conflict", "message": error_msg})
    await _write_oscar_audit(
        db, request, "demographic", f"{absorbed_no}->{demographic_no}", "merge"
    )
    return {"message": f"Patient {absorbed_no} successfully merged into {demographic_no}"}
