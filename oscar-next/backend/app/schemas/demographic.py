"""
Pydantic schemas for Demographics — input validation, API responses, FHIR Patient mapping.

PHIPA/PIPEDA constraint enforced here:
  `sin` is NEVER included in any response schema — not exposed by any API endpoint.
"""
from __future__ import annotations

from datetime import date, datetime
from typing import Any, Optional
from pydantic import BaseModel, ConfigDict, field_validator, model_validator


# ── Province / territory enum values ──────────────────────────────────────────
CANADIAN_PROVINCES = {
    "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT",
}

SEX_TO_FHIR = {"M": "male", "F": "female", "O": "other", "U": "unknown",
               "T": "unknown", "I": "unknown", "": "unknown"}

PATIENT_STATUS_LABELS = {
    "AC": "Active", "IN": "Inactive", "DE": "Deceased",
    "MO": "Moved Out", "NE": "Newborn", "SP": "Suspended",
}


# ── Ext field (demographicExt) ─────────────────────────────────────────────────

class ExtFieldResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    key_val: Optional[str] = None
    value: Optional[str] = None
    date_time: Optional[datetime] = None


# ── Contact schemas ────────────────────────────────────────────────────────────

class ContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    type: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    residencePhone: Optional[str] = None
    cellPhone: Optional[str] = None
    workPhone: Optional[str] = None
    email: Optional[str] = None
    fax: Optional[str] = None
    specialty: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal: Optional[str] = None


class DemographicContactResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    contactId: Optional[str] = None
    role: Optional[str] = None
    sdm: Optional[str] = None
    ec: Optional[str] = None
    mrp: Optional[int] = None
    health_care_team: Optional[int] = None
    best_contact: Optional[str] = None
    category: Optional[str] = None
    note: Optional[str] = None
    active: Optional[int] = None
    consentToContact: Optional[int] = None
    contact: Optional[ContactResponse] = None


class DemographicContactCreate(BaseModel):
    contactId: str
    role: Optional[str] = None
    sdm: Optional[str] = None
    ec: Optional[str] = None
    mrp: Optional[int] = None
    health_care_team: Optional[int] = None
    best_contact: Optional[str] = None
    category: Optional[str] = None
    note: Optional[str] = None


# ── Consent schemas ────────────────────────────────────────────────────────────

class ConsentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    consent_type_id: Optional[int] = None
    explicit: Optional[int] = None
    optout: Optional[int] = None
    last_entered_by: Optional[str] = None
    consent_date: Optional[datetime] = None
    optout_date: Optional[datetime] = None
    edit_date: Optional[datetime] = None


class ConsentCreate(BaseModel):
    consent_type_id: int
    explicit: int = 0
    optout: int = 0


# ── Merge schemas ──────────────────────────────────────────────────────────────

class MergeHistoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    demographic_no: int
    merged_to: int
    deleted: int
    lastUpdateUser: Optional[str] = None
    lastUpdateDate: Optional[date] = None


# ── Core demographic schemas ───────────────────────────────────────────────────

class DemographicCreate(BaseModel):
    first_name: str
    last_name: str
    sex: str
    year_of_birth: Optional[str] = None
    month_of_birth: Optional[str] = None
    date_of_birth: Optional[str] = None
    title: Optional[str] = None
    middle_names: Optional[str] = None
    alias: Optional[str] = None
    pref_name: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    email: Optional[str] = None
    consentToUseEmailForCare: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal: Optional[str] = None
    residentialAddress: Optional[str] = None
    residentialCity: Optional[str] = None
    residentialProvince: Optional[str] = None
    residentialPostal: Optional[str] = None
    hin: Optional[str] = None
    ver: Optional[str] = None
    hc_type: Optional[str] = None
    hc_renew_date: Optional[date] = None
    roster_status: Optional[str] = None
    roster_date: Optional[date] = None
    roster_enrolled_to: Optional[str] = None
    patient_status: Optional[str] = "AC"
    provider_no: Optional[str] = None
    chart_no: Optional[str] = None
    official_lang: Optional[str] = None
    spoken_lang: Optional[str] = None
    citizenship: Optional[str] = None
    country_of_origin: Optional[str] = None

    @field_validator("first_name", "last_name")
    @classmethod
    def not_empty(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("must not be blank")
        return v.strip()

    @field_validator("sex")
    @classmethod
    def valid_sex(cls, v: str) -> str:
        allowed = {"M", "F", "O", "U", "T", "I"}
        if v.upper() not in allowed:
            raise ValueError(f"sex must be one of {allowed}")
        return v.upper()


class DemographicUpdate(BaseModel):
    """Partial update — all fields optional."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    sex: Optional[str] = None
    title: Optional[str] = None
    middle_names: Optional[str] = None
    alias: Optional[str] = None
    pref_name: Optional[str] = None
    year_of_birth: Optional[str] = None
    month_of_birth: Optional[str] = None
    date_of_birth: Optional[str] = None
    phone: Optional[str] = None
    phone2: Optional[str] = None
    email: Optional[str] = None
    consentToUseEmailForCare: Optional[int] = None
    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal: Optional[str] = None
    residentialAddress: Optional[str] = None
    residentialCity: Optional[str] = None
    residentialProvince: Optional[str] = None
    residentialPostal: Optional[str] = None
    hin: Optional[str] = None
    ver: Optional[str] = None
    hc_type: Optional[str] = None
    hc_renew_date: Optional[date] = None
    roster_status: Optional[str] = None
    roster_date: Optional[date] = None
    roster_termination_date: Optional[date] = None
    roster_termination_reason: Optional[str] = None
    roster_enrolled_to: Optional[str] = None
    patient_status: Optional[str] = None
    patient_status_date: Optional[date] = None
    provider_no: Optional[str] = None
    chart_no: Optional[str] = None
    official_lang: Optional[str] = None
    spoken_lang: Optional[str] = None
    citizenship: Optional[str] = None
    country_of_origin: Optional[str] = None
    anonymous: Optional[str] = None
    newsletter: Optional[str] = None
    children: Optional[str] = None
    sourceOfIncome: Optional[str] = None
    pcn_indicator: Optional[str] = None


class DemographicResponse(BaseModel):
    """Flat Oscar-style patient response. Never includes sin."""
    model_config = ConfigDict(from_attributes=True)

    demographic_no: int
    title: Optional[str] = None
    first_name: str
    last_name: str
    middle_names: Optional[str] = None
    alias: Optional[str] = None
    pref_name: Optional[str] = None
    sex: str
    dob_iso: Optional[str] = None
    age: Optional[int] = None

    phone: Optional[str] = None
    phone2: Optional[str] = None
    email: Optional[str] = None
    consentToUseEmailForCare: Optional[int] = None

    address: Optional[str] = None
    city: Optional[str] = None
    province: Optional[str] = None
    postal: Optional[str] = None
    previousAddress: Optional[str] = None

    residentialAddress: Optional[str] = None
    residentialCity: Optional[str] = None
    residentialProvince: Optional[str] = None
    residentialPostal: Optional[str] = None

    hin: Optional[str] = None
    ver: Optional[str] = None
    hc_type: Optional[str] = None
    hc_renew_date: Optional[date] = None

    roster_status: Optional[str] = None
    roster_date: Optional[date] = None
    roster_termination_date: Optional[date] = None
    roster_termination_reason: Optional[str] = None
    roster_enrolled_to: Optional[str] = None

    patient_status: Optional[str] = None
    patient_status_label: Optional[str] = None
    patient_status_date: Optional[date] = None
    date_joined: Optional[date] = None
    end_date: Optional[date] = None

    provider_no: Optional[str] = None
    family_doctor: Optional[str] = None
    family_physician: Optional[str] = None

    chart_no: Optional[str] = None
    official_lang: Optional[str] = None
    spoken_lang: Optional[str] = None
    citizenship: Optional[str] = None
    country_of_origin: Optional[str] = None
    pcn_indicator: Optional[str] = None
    anonymous: Optional[str] = None
    newsletter: Optional[str] = None
    children: Optional[str] = None
    sourceOfIncome: Optional[str] = None
    myOscarUserName: Optional[str] = None

    lastUpdateUser: Optional[str] = None
    lastUpdateDate: Optional[datetime] = None

    @classmethod
    def from_orm_with_computed(cls, obj) -> "DemographicResponse":
        from sqlalchemy import inspect as sa_inspect
        mapper = sa_inspect(type(obj))
        # Use mapper attr names (Python side) not column keys (DB side) to handle renamed cols
        data = {
            attr.key: getattr(obj, attr.key)
            for attr in mapper.mapper.column_attrs
            if attr.key != "sin"
        }
        data["dob_iso"] = obj.dob_iso
        data["age"] = obj.age
        data["patient_status_label"] = PATIENT_STATUS_LABELS.get(obj.patient_status or "", None)
        return cls.model_validate(data)


class PatientBannerResponse(BaseModel):
    """Lightweight banner — name, identifiers, alert counts. Never includes sin."""
    demographic_no: int
    display_name: str
    pref_name: Optional[str] = None
    dob_iso: Optional[str] = None
    age: Optional[int] = None
    sex: Optional[str] = None
    hin: Optional[str] = None
    hc_type: Optional[str] = None
    hc_renew_date: Optional[date] = None
    chart_no: Optional[str] = None
    patient_status: Optional[str] = None
    patient_status_label: Optional[str] = None
    allergy_count: int = 0
    critical_allergy: bool = False
    active_rx_count: int = 0
    provider_no: Optional[str] = None
    roster_status: Optional[str] = None


class DuplicateCandidate(BaseModel):
    demographic_no: int
    first_name: str
    last_name: str
    dob_iso: Optional[str] = None
    hin: Optional[str] = None
    chart_no: Optional[str] = None
    patient_status: Optional[str] = None
    score: int


class DuplicateCheckResponse(BaseModel):
    has_duplicates: bool
    candidates: list[DuplicateCandidate] = []


class PatientSearchResult(BaseModel):
    demographic_no: int
    first_name: str
    last_name: str
    pref_name: Optional[str] = None
    dob_iso: Optional[str] = None
    age: Optional[int] = None
    hin: Optional[str] = None
    chart_no: Optional[str] = None
    patient_status: Optional[str] = None
    patient_status_label: Optional[str] = None
    provider_no: Optional[str] = None


class PatientSearchResponse(BaseModel):
    total: int
    page: int
    limit: int
    results: list[PatientSearchResult]


class MergeRequest(BaseModel):
    """Request to merge absorbed_id into surviving_id (caller provides surviving via URL)."""
    reason: Optional[str] = None


# ── FHIR Patient builder ───────────────────────────────────────────────────────

def demographic_to_fhir_patient(d, fhir_base_url: str = "") -> dict[str, Any]:
    """
    Convert a Demographic ORM object to a FHIR R4 Patient resource dict.
    Validated against fhir.resources==7.1.0 structure but returned as plain dict
    for FastAPI JSONResponse (avoids double-serialization overhead).
    Never includes sin.
    """
    identifiers = []
    if d.hin:
        identifiers.append({
            "use": "official",
            "system": "https://health.gov.on.ca/en/pro/programs/ohip/",
            "value": d.hin,
            "version": d.ver or "",
        })
    if d.chart_no:
        identifiers.append({
            "use": "secondary",
            "system": f"{fhir_base_url}/NamingSystem/chart-no",
            "value": d.chart_no,
        })
    if d.demographic_no:
        identifiers.append({
            "use": "usual",
            "system": f"{fhir_base_url}/NamingSystem/demographic-no",
            "value": str(d.demographic_no),
        })

    names = []
    given = [n for n in [d.first_name, d.middle_names] if n]
    names.append({
        "use": "official",
        "family": d.last_name,
        "given": given,
        "text": f"{d.first_name} {d.last_name}",
    })
    if d.pref_name:
        names.append({"use": "nickname", "text": d.pref_name})

    telecoms = []
    if d.phone:
        telecoms.append({"system": "phone", "value": d.phone, "use": "home"})
    if d.phone2:
        telecoms.append({"system": "phone", "value": d.phone2, "use": "mobile"})
    if d.email:
        telecoms.append({"system": "email", "value": d.email, "use": "home"})

    addresses = []
    if any([d.address, d.city, d.province, d.postal]):
        addresses.append({
            "use": "home",
            "type": "postal",
            "line": [d.address] if d.address else [],
            "city": d.city or "",
            "state": d.province or "",
            "postalCode": d.postal or "",
            "country": "CA",
        })
    # Add residential address only if it differs from mailing
    if d.residentialAddress and d.residentialAddress != d.address:
        addresses.append({
            "use": "home",
            "type": "physical",
            "line": [d.residentialAddress] if d.residentialAddress else [],
            "city": d.residentialCity or "",
            "state": d.residentialProvince or "",
            "postalCode": d.residentialPostal or "",
            "country": "CA",
        })

    communication = []
    for lang_field in [d.official_lang, d.spoken_lang]:
        if lang_field:
            # Convert Oscar language names to BCP 47 codes (best-effort)
            lang_code = _oscar_lang_to_bcp47(lang_field)
            if lang_code and not any(c.get("language", {}).get("coding", [{}])[0].get("code") == lang_code for c in communication):
                communication.append({
                    "language": {
                        "coding": [{"system": "urn:ietf:bcp:47", "code": lang_code}],
                        "text": lang_field,
                    },
                    "preferred": lang_field == d.official_lang,
                })

    gp = []
    if d.provider_no:
        gp.append({"reference": f"Practitioner/{d.provider_no}"})

    patient: dict[str, Any] = {
        "resourceType": "Patient",
        "id": str(d.demographic_no),
        "meta": {"lastUpdated": d.lastUpdateDate.isoformat() if d.lastUpdateDate else None},
        "identifier": identifiers,
        "active": d.is_active,
        "name": names,
        "telecom": telecoms,
        "gender": SEX_TO_FHIR.get(d.sex, "unknown"),
        "address": addresses,
        "generalPractitioner": gp,
    }
    if d.dob_iso:
        patient["birthDate"] = d.dob_iso
    if communication:
        patient["communication"] = communication

    # Extension: patient status (Oscar-specific)
    if d.patient_status:
        patient.setdefault("extension", []).append({
            "url": "https://oscar.oscar-emr.com/fhir/StructureDefinition/patient-status",
            "valueString": d.patient_status,
        })
    if d.roster_status:
        patient.setdefault("extension", []).append({
            "url": "https://oscar.oscar-emr.com/fhir/StructureDefinition/roster-status",
            "valueString": d.roster_status,
        })

    return patient


def _oscar_lang_to_bcp47(oscar_lang: str) -> str | None:
    mapping = {
        "English": "en", "French": "fr", "Cantonese": "yue", "Mandarin": "cmn",
        "Spanish": "es", "Punjabi": "pa", "Tagalog": "tl", "Arabic": "ar",
        "Portuguese": "pt", "Tamil": "ta", "Hindi": "hi", "Urdu": "ur",
        "Korean": "ko", "Italian": "it", "Russian": "ru", "German": "de",
        "Japanese": "ja", "Vietnamese": "vi", "Polish": "pl",
    }
    return mapping.get(oscar_lang)
