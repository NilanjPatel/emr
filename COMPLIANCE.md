# Compliance Requirements — HIPAA / PIPEDA / PHIPA

## Jurisdiction

This system serves Canadian primary care clinics, primarily Ontario. Applicable legislation:
- **PHIPA** (Personal Health Information Protection Act) — Ontario — primary
- **PIPEDA** (Personal Information Protection and Electronic Documents Act) — federal — secondary
- **HIPAA** (US) — applies only if US patient data is ever processed — treat as reference standard
- **Health Canada Digital Health** regulatory guidance — AI/clinical decision support

---

## Mandatory Requirements (Non-Negotiable)

### 1. Audit Trail
- **Requirement:** Every access to personal health information must be logged with: user, timestamp, action, resource type, resource ID, patient ID
- **Implementation:** FastAPI middleware writes to existing `oscar_log` table on every request that returns patient data
- **Table:** `oscar_log` (existing MariaDB table — do not alter schema)
- **Retention:** 10 years minimum (PHIPA requirement)
- **Status:** ☐ Not implemented — **Phase 0 gate: must complete before any patient endpoint ships**

### 2. Authentication
- **Requirement:** All users must authenticate before accessing any patient data
- **Implementation:** Keycloak 24 with SMART on FHIR. JWT RS256 tokens.
- **Access token TTL:** 15 minutes maximum
- **Session:** Refresh token in `httpOnly` cookie only (never localStorage)
- **Status:** ☐ Not implemented

### 3. Multi-Factor Authentication
- **Requirement:** MFA required for all roles with prescribing, billing, or admin access
- **Mandatory roles:** `doctor`, `nurse_practitioner`, `admin`, `billing_admin`
- **Implementation:** Keycloak TOTP (Google Authenticator compatible)
- **Status:** ☐ Not implemented

### 4. Encryption in Transit
- **Requirement:** All data in transit encrypted with TLS 1.2 minimum (TLS 1.3 preferred)
- **Implementation:** Nginx TLS termination — already present in docker-compose volumes (ssl.crt/ssl.key)
- **Scope:** All HTTP traffic. Internal Docker network traffic on `back-tier` is acceptable unencrypted.
- **Status:** ☐ Not verified for new stack

### 5. Encryption at Rest
- **Requirement:** Patient data encrypted at rest
- **Implementation:** MariaDB TDE — `innodb_encrypt_tables=ON` at the engine level
- **Action needed:** Enable in `docker/db/my.cnf` — zero application change
- **Documents:** OscarDocument filesystem encrypted via LUKS or cloud volume encryption
- **Status:** ☐ Not implemented

### 6. Role-Based Access Control
- **Requirement:** Users can only access data their role permits
- **Implementation:** FastAPI RBAC middleware reads `secRole`/`secObjPrivilege` tables, maps to Keycloak roles, enforces SMART on FHIR scopes
- **Granularity:** Read vs. write vs. admin per resource type
- **Status:** ☐ Not implemented

### 7. Data Residency
- **Requirement:** All Canadian patient data must remain in Canada (PIPEDA)
- **Implementation:** 
  - Docker: self-hosted within clinic or Canadian data center
  - Cloud: AWS ca-central-1 or OCI Toronto only
  - AI: On-premise Ollama for real-time PHI processing; no PHI sent to US-hosted LLMs without de-identification
- **Status:** ☐ Policy confirmed, infrastructure not yet set up

### 8. Breach Notification
- **Requirement:** PHIPA requires notification to Information and Privacy Commissioner of Ontario within 72 hours of a significant breach
- **Implementation:** Audit log monitoring. Anomaly detection (e.g., bulk record access) to be added to AI sidecar.
- **Status:** ☐ Not implemented

---

## AI-Specific Requirements (Health Canada Guidance)

### AI as Clinical Decision Support — Not a Medical Device
- AI output must always be labeled as a suggestion
- Clinician must explicitly approve before any AI output is persisted
- AI suggestions must not be auto-saved under any circumstances
- AI system must log: what was suggested, whether it was accepted or rejected, by whom, timestamp

### PHI De-identification Before External LLM
When using Anthropic Claude API (or any external LLM):
1. Run de-identification pipeline stripping all 18 HIPAA Safe Harbor identifiers:
   - Names, geographic data, dates (except year), phone, fax, email, SSN, health card numbers, account numbers, certificate/license numbers, VIN, device identifiers, URLs, IP addresses, biometric identifiers, photos, unique identifiers
2. Log that de-identification occurred
3. Never cache identifiable data in external LLM context
- **Status:** ☐ De-identification pipeline not built

### Local LLM for Real-Time Features
- Ambient charting, encounter assist → Ollama on clinic network
- No PHI leaves the clinic network for real-time features
- **Status:** ☐ Not implemented

---

## Per-Endpoint Compliance Checklist

Every endpoint that returns or modifies patient data must satisfy ALL of these before shipping:

- [ ] JWT authentication enforced (401 without valid token)
- [ ] RBAC enforced (403 for insufficient role/scope)
- [ ] Audit log entry written to `oscar_log` table
- [ ] Response does not include more data than the scope permits
- [ ] TLS enforced at Nginx (HTTPS only)
- [ ] Input validated (no SQL injection possible via SQLAlchemy ORM)
- [ ] No PHI in URL parameters (use POST body or FHIR search params)
- [ ] No PHI in application logs (log resource IDs, not content)

---

## Secrets Management

| Secret | Current Location | Target Location |
|---|---|---|
| MariaDB password | `docker-compose.yml` plaintext | HashiCorp Vault or AWS Secrets Manager |
| `oscar.properties` DB credentials | Volume mount plaintext | Vault |
| SSL certificates | Volume mounts | Vault PKI or AWS Certificate Manager |
| Keycloak admin password | To be created | Vault |
| Anthropic API key | To be created | Vault |

**Status:** ☐ All secrets still in plaintext in docker-compose — must migrate in Phase 0

---

## Penetration Testing Schedule

- After Phase 0 (Keycloak cutover): full pentest of auth layer
- After Phase 2 (Patient demographics live): pentest of patient data endpoints
- After Phase 6 (Billing live): pentest of billing + financial data
- After Phase 10 (WAR decommissioned): final pentest of complete new system

---

## Compliance Status Summary

| Requirement | Status | Phase |
|---|---|---|
| Audit trail middleware | ☐ Not started | Phase 0 |
| Keycloak authentication | ☐ Not started | Phase 0 |
| MFA for clinical roles | ☐ Not started | Phase 0 |
| TLS 1.3 at Nginx | ☐ Not verified | Phase 0 |
| MariaDB TDE | ☐ Not started | Phase 0 |
| RBAC middleware | ☐ Not started | Phase 0 |
| Secrets in Vault | ☐ Not started | Phase 0 |
| PHI de-identification pipeline | ☐ Not started | Phase 3 (before AI goes live) |
| On-premise LLM (Ollama) | ☐ Not started | Phase 3 |
| AI suggestion audit log | ☐ Not started | Phase 3 |
| Breach monitoring | ☐ Not started | Phase 5 |
| Penetration test (auth) | ☐ Not started | After Phase 0 |
