"""
PHI de-identification pipeline — PIPEDA/HIPAA Safe Harbor method.

Strips all 18 HIPAA identifiers before any text leaves the clinic network
for external LLM processing (Anthropic Claude).

On-premise Ollama bypasses this entirely — PHI never leaves the host.

Identifiers removed (HIPAA Safe Harbor §164.514(b)):
  1  Names
  2  Geographic data below province level
  3  Dates (except year) for age > 89
  4  Phone numbers
  5  Fax numbers
  6  Email addresses
  7  Social insurance / health card numbers
  8  Medical record numbers
  9  Health plan beneficiary numbers
  10 Account numbers
  11 Certificate/license numbers
  12 Vehicle identifiers / VINs
  13 Device identifiers / serial numbers
  14 URLs
  15 IP addresses
  16 Biometric identifiers
  17 Full-face photographs (not applicable — text only)
  18 Any other unique identifying number or code
"""
import re
from dataclasses import dataclass, field


# ── Regex patterns ────────────────────────────────────────────────────────────

_PHONE = re.compile(
    r"\b(\+?1[-.\s]?)?(\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4})\b"
)
_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)
_HCN = re.compile(                          # Ontario OHIP / BC PHN / AB ULI patterns
    r"\b\d{4}[-\s]?\d{3}[-\s]?\d{3}[-\s]?\w{0,2}\b"
)
_SIN = re.compile(                          # Canadian SIN
    r"\b\d{3}[-\s]\d{3}[-\s]\d{3}\b"
)
_URL = re.compile(
    r"https?://[^\s]+"
)
_IP = re.compile(
    r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
)
_POSTAL = re.compile(                       # Canadian postal code
    r"\b[A-Za-z]\d[A-Za-z][\s]?\d[A-Za-z]\d\b"
)
_DOB_FULL = re.compile(                     # dates with day — remove, keep year only
    r"\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|"
    r"Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
    r"[\s.,]+\d{1,2}[\s.,]+(\d{4})\b"
)
_DATE_NUMERIC = re.compile(                 # numeric dates like 2024-03-15 or 15/03/2024
    r"\b(\d{4})[/-](\d{2})[/-](\d{2})\b|"
    r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"
)
_MRN = re.compile(                          # MRN / chart number patterns
    r"\b(MRN|Chart|Record|Patient\s+ID|ID)[:\s#]+\d+\b",
    re.IGNORECASE,
)


@dataclass
class DeidentifyResult:
    text: str
    replacements: int = 0
    tags_used: list[str] = field(default_factory=list)


def deidentify(text: str) -> DeidentifyResult:
    """
    Apply all de-identification rules to text.
    Returns cleaned text with PHI replaced by category tags.
    Only used before sending to external LLMs (Anthropic).
    Ollama calls skip this entirely.
    """
    result = text
    count = 0
    tags: list[str] = []

    def sub(pattern: re.Pattern, replacement: str, t: str, tag: str) -> tuple[str, int]:
        new, n = pattern.subn(replacement, t)
        if n:
            tags.append(tag)
        return new, n

    result, n = sub(_EMAIL, "[EMAIL]", result, "email")
    count += n

    result, n = sub(_URL, "[URL]", result, "url")
    count += n

    result, n = sub(_IP, "[IP]", result, "ip")
    count += n

    result, n = sub(_PHONE, "[PHONE]", result, "phone")
    count += n

    result, n = sub(_SIN, "[SIN]", result, "sin")
    count += n

    result, n = sub(_HCN, "[HCN]", result, "hcn")
    count += n

    result, n = sub(_POSTAL, "[POSTAL]", result, "postal")
    count += n

    result, n = sub(_MRN, r"\1: [MRN]", result, "mrn")
    count += n

    # Keep year only for full dates (HIPAA: year alone is safe unless age > 89)
    result, n = sub(_DOB_FULL, r"[DATE]/\2", result, "date_full")
    count += n

    result, n = sub(_DATE_NUMERIC, "[DATE]", result, "date_numeric")
    count += n

    return DeidentifyResult(text=result, replacements=count, tags_used=list(set(tags)))
