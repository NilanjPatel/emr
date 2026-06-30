"""Tests for the PHI de-identification pipeline."""
import pytest

from app.services.deidentify import deidentify


def test_email_removed():
    result = deidentify("Contact john.doe@example.com for details.")
    assert "[EMAIL]" in result.text
    assert "john.doe@example.com" not in result.text
    assert result.replacements >= 1


def test_phone_removed():
    result = deidentify("Call the clinic at 416-555-1234.")
    assert "[PHONE]" in result.text
    assert "416-555-1234" not in result.text


def test_sin_removed():
    result = deidentify("Patient SIN: 123-456-789.")
    assert "[SIN]" in result.text
    assert "123-456-789" not in result.text


def test_url_removed():
    result = deidentify("See https://example.com/patient/123 for records.")
    assert "[URL]" in result.text
    assert "https://example.com" not in result.text


def test_ip_removed():
    result = deidentify("Server at 192.168.1.100 responded.")
    assert "[IP]" in result.text
    assert "192.168.1.100" not in result.text


def test_postal_code_removed():
    result = deidentify("Patient lives at M5V 3A8.")
    assert "[POSTAL]" in result.text
    assert "M5V 3A8" not in result.text


def test_numeric_date_removed():
    result = deidentify("DOB: 1985-03-15.")
    assert "[DATE]" in result.text
    assert "1985-03-15" not in result.text


def test_full_date_year_preserved():
    result = deidentify("Born March 15, 1985.")
    assert "1985" in result.text       # year kept
    assert "March 15" not in result.text


def test_mrn_removed():
    result = deidentify("MRN: 987654 has been admitted.")
    assert "[MRN]" in result.text
    assert "987654" not in result.text


def test_clean_text_unchanged():
    text = "Patient reports persistent cough for two weeks. No fever."
    result = deidentify(text)
    assert result.text == text
    assert result.replacements == 0


def test_multiple_phi_types():
    text = "Patient Jane Smith, DOB 1990-01-01, HCN 1234 567 890, email jane@clinic.ca"
    result = deidentify(text)
    assert "jane@clinic.ca" not in result.text
    assert "1990-01-01" not in result.text
    assert result.replacements >= 2


def test_tags_used_reported():
    result = deidentify("Email: test@test.com and phone 416-555-0000")
    assert "email" in result.tags_used
    assert "phone" in result.tags_used
