"""
Phase 1 — Demographic model tests.

Tests Demographic ORM properties and FHIR Patient mapping.
All tests are unit-only (no live DB required) using mock objects.
"""
import pytest
from unittest.mock import MagicMock
from datetime import date

from app.models.demographic import Demographic
from app.schemas.demographic import demographic_to_fhir_patient, SEX_TO_FHIR


def _make_demographic(**kwargs) -> Demographic:
    d = Demographic()
    defaults = {
        "demographic_no": 1001,
        "first_name": "Jane",
        "last_name": "Smith",
        "sex": "F",
        "year_of_birth": "1985",
        "month_of_birth": "01",
        "date_of_birth": "15",
        "patient_status": "AC",
        "end_date": None,
        "lastUpdateDate": None,
        "hin": None,
        "ver": None,
        "chart_no": None,
        "phone": None,
        "phone2": None,
        "email": None,
        "address": None,
        "city": None,
        "province": None,
        "postal": None,
        "residentialAddress": None,
        "residentialCity": None,
        "residentialProvince": None,
        "residentialPostal": None,
        "pref_name": None,
        "middle_names": None,
        "provider_no": None,
        "official_lang": None,
        "spoken_lang": None,
        "roster_status": None,
    }
    defaults.update(kwargs)
    for k, v in defaults.items():
        setattr(d, k, v)
    return d


# ── dob_iso property ───────────────────────────────────────────────────────────

def test_dob_iso_valid():
    d = _make_demographic(year_of_birth="1985", month_of_birth="01", date_of_birth="15")
    assert d.dob_iso == "1985-01-15"


def test_dob_iso_zero_year():
    d = _make_demographic(year_of_birth="0000", month_of_birth="01", date_of_birth="15")
    assert d.dob_iso is None


def test_dob_iso_zero_month():
    d = _make_demographic(year_of_birth="1990", month_of_birth="0", date_of_birth="1")
    assert d.dob_iso is None


def test_dob_iso_none_fields():
    d = _make_demographic(year_of_birth=None, month_of_birth=None, date_of_birth=None)
    assert d.dob_iso is None


def test_dob_iso_blank_strings():
    d = _make_demographic(year_of_birth="", month_of_birth="", date_of_birth="")
    assert d.dob_iso is None


def test_dob_iso_single_digit_month_and_day():
    d = _make_demographic(year_of_birth="2000", month_of_birth="3", date_of_birth="7")
    assert d.dob_iso == "2000-03-07"


# ── age property ───────────────────────────────────────────────────────────────

def test_age_returns_integer():
    d = _make_demographic(year_of_birth="1985", month_of_birth="01", date_of_birth="01")
    age = d.age
    assert isinstance(age, int)
    assert age >= 39


def test_age_none_when_no_dob():
    d = _make_demographic(year_of_birth=None, month_of_birth=None, date_of_birth=None)
    assert d.age is None


# ── is_active property ─────────────────────────────────────────────────────────

def test_is_active_when_ac_and_no_end_date():
    d = _make_demographic(patient_status="AC", end_date=None)
    assert d.is_active is True


def test_not_active_when_deceased():
    d = _make_demographic(patient_status="DE", end_date=None)
    assert d.is_active is False


def test_not_active_when_end_date_set():
    d = _make_demographic(patient_status="AC", end_date=date(2023, 1, 1))
    assert d.is_active is False


# ── FHIR Patient mapping ───────────────────────────────────────────────────────

def test_fhir_patient_resource_type():
    d = _make_demographic()
    fhir = demographic_to_fhir_patient(d)
    assert fhir["resourceType"] == "Patient"


def test_fhir_patient_id_is_demographic_no_as_string():
    d = _make_demographic(demographic_no=42)
    fhir = demographic_to_fhir_patient(d)
    assert fhir["id"] == "42"


def test_fhir_patient_official_name():
    d = _make_demographic(first_name="John", last_name="Doe", middle_names="Michael")
    fhir = demographic_to_fhir_patient(d)
    official = next(n for n in fhir["name"] if n["use"] == "official")
    assert official["family"] == "Doe"
    assert "John" in official["given"]
    assert "Michael" in official["given"]


def test_fhir_patient_nickname_when_pref_name():
    d = _make_demographic(pref_name="Johnny")
    fhir = demographic_to_fhir_patient(d)
    nicknames = [n for n in fhir["name"] if n["use"] == "nickname"]
    assert len(nicknames) == 1
    assert nicknames[0]["text"] == "Johnny"


def test_fhir_patient_no_nickname_without_pref_name():
    d = _make_demographic(pref_name=None)
    fhir = demographic_to_fhir_patient(d)
    nicknames = [n for n in fhir["name"] if n["use"] == "nickname"]
    assert len(nicknames) == 0


def test_fhir_gender_mapping_male():
    d = _make_demographic(sex="M")
    fhir = demographic_to_fhir_patient(d)
    assert fhir["gender"] == "male"


def test_fhir_gender_mapping_female():
    d = _make_demographic(sex="F")
    fhir = demographic_to_fhir_patient(d)
    assert fhir["gender"] == "female"


def test_fhir_gender_mapping_unknown():
    for unknown_sex in ["U", "T", "I", ""]:
        d = _make_demographic(sex=unknown_sex)
        fhir = demographic_to_fhir_patient(d)
        assert fhir["gender"] == "unknown", f"Expected unknown for sex={unknown_sex!r}"


def test_fhir_patient_active_when_ac():
    d = _make_demographic(patient_status="AC", end_date=None)
    fhir = demographic_to_fhir_patient(d)
    assert fhir["active"] is True


def test_fhir_patient_inactive_when_de():
    d = _make_demographic(patient_status="DE")
    fhir = demographic_to_fhir_patient(d)
    assert fhir["active"] is False


def test_fhir_patient_hin_identifier():
    d = _make_demographic(hin="1234567890", ver="AB", hc_type="ON")
    fhir = demographic_to_fhir_patient(d)
    hin_id = next((i for i in fhir["identifier"] if i.get("system", "").endswith("ohip/")), None)
    assert hin_id is not None
    assert hin_id["value"] == "1234567890"
    assert hin_id["version"] == "AB"


def test_fhir_patient_no_hin_identifier_when_empty():
    d = _make_demographic(hin=None)
    fhir = demographic_to_fhir_patient(d)
    hin_ids = [i for i in fhir["identifier"] if "ohip" in i.get("system", "")]
    assert len(hin_ids) == 0


def test_fhir_patient_sin_never_included():
    d = _make_demographic()
    d.sin = "123-456-789"
    fhir = demographic_to_fhir_patient(d)
    import json
    fhir_str = json.dumps(fhir)
    assert "sin" not in fhir_str.lower()
    assert "123-456-789" not in fhir_str


def test_fhir_patient_birthdate():
    d = _make_demographic(year_of_birth="1990", month_of_birth="06", date_of_birth="15")
    fhir = demographic_to_fhir_patient(d)
    assert fhir["birthDate"] == "1990-06-15"


def test_fhir_patient_no_birthdate_when_zero_dob():
    d = _make_demographic(year_of_birth="0000", month_of_birth="00", date_of_birth="00")
    fhir = demographic_to_fhir_patient(d)
    assert "birthDate" not in fhir


def test_fhir_patient_general_practitioner():
    d = _make_demographic(provider_no="999")
    fhir = demographic_to_fhir_patient(d)
    assert len(fhir["generalPractitioner"]) == 1
    assert fhir["generalPractitioner"][0]["reference"] == "Practitioner/999"


def test_fhir_patient_telecom_phone():
    d = _make_demographic(phone="416-555-1234", phone2="647-555-9876", email="jane@example.com")
    fhir = demographic_to_fhir_patient(d)
    systems = [(t["system"], t["value"]) for t in fhir["telecom"]]
    assert ("phone", "416-555-1234") in systems
    assert ("phone", "647-555-9876") in systems
    assert ("email", "jane@example.com") in systems


def test_fhir_patient_address_mailing():
    d = _make_demographic(address="123 Main St", city="Toronto", province="ON", postal="M5V 1A1")
    fhir = demographic_to_fhir_patient(d)
    addr = next((a for a in fhir["address"] if a.get("type") == "postal"), None)
    assert addr is not None
    assert "123 Main St" in addr["line"]
    assert addr["city"] == "Toronto"
    assert addr["state"] == "ON"
    assert addr["postalCode"] == "M5V 1A1"
    assert addr["country"] == "CA"


def test_fhir_patient_extension_has_patient_status():
    d = _make_demographic(patient_status="AC")
    fhir = demographic_to_fhir_patient(d)
    extensions = fhir.get("extension", [])
    status_ext = next(
        (e for e in extensions if "patient-status" in e.get("url", "")), None
    )
    assert status_ext is not None
    assert status_ext["valueString"] == "AC"
