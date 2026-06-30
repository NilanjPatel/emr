# Technology Stack — Decisions and Rationale

## Core Decisions (All Confirmed by User)

### Backend: Python 3.12 + FastAPI
- Full rewrite (Path B) — not preserving Java backend
- FastAPI chosen for: minimal boilerplate, async-native, auto OpenAPI docs, excellent AI/ML ecosystem
- SQLAlchemy 2.0 async for DB access — reflects existing MariaDB schema, no migrations
- Pydantic v2 for data validation and FHIR resource modeling

### API Standard: FHIR R4
- Replaces all custom REST endpoints for clinical data
- Replaces all SOAP integrations (except temporary MCEDT adapter)
- `fhir.resources` library (Pydantic-based) for resource modeling and validation
- HAPI FHIR validator for integration testing
- Base URL: `https://<clinic>/fhir/R4/`

### Frontend: Next.js 14 App Router + TypeScript
- TailwindCSS + shadcn/ui for modern, accessible component library
- `@tanstack/react-query` for server state management
- `react-hook-form` + `zod` for complex clinical forms
- `@fullcalendar/react` for scheduling views
- `Tiptap` for encounter note rich text editing
- `date-fns` for Canadian date handling

### Auth: Keycloak 24 (self-hosted) + SMART on FHIR
- Self-hosted mandatory — PIPEDA/PHIPA Canadian data residency
- SMART on FHIR = OAuth 2.0 profile designed for healthcare (replaces Oscar's OAuth 1.0)
- RS256 JWT: 15-minute access tokens, 8-hour refresh tokens in `httpOnly` cookie
- LDAP federation: replaces `LdapLoginModule.java` (same LDAP server, new client)
- MFA (TOTP): mandatory for `doctor`, `admin`, `billing_admin` Keycloak roles
- Existing `secRole`/`secObjPrivilege` tables → Keycloak roles via sync job

### AI: FastAPI sidecar + Anthropic Claude + Ollama
- Separate container from the main backend
- On-premise Ollama (Llama 3.3 / Mistral-Medical): real-time in-encounter features — PHI never leaves clinic network
- Anthropic Claude API: async non-real-time tasks (summarization, referral letters) — PHI de-identified before sending
- AI endpoints: suggestion only — no auto-save, no auto-action
- De-identification pipeline strips all 18 HIPAA/PIPEDA identifiers before any external LLM call

### Database: MariaDB 10.5 (unchanged)
- **Schema frozen** — SQLAlchemy models use `autoload_with` to reflect existing tables
- No Alembic migrations that touch existing tables
- New-system-only tables (e.g., AI suggestion audit, Keycloak session cache) are isolated in a separate schema `oscar_next`
- Connection: same MariaDB instance, same credentials, same `oscar` database

### Infrastructure
- Docker Compose extended from existing (MariaDB preserved, Oscar WAR decommissioned — no side-by-side running)
- New containers: `oscar-api` (FastAPI), `oscar-web` (Next.js/Node), `oscar-ai` (FastAPI), `keycloak`, `keycloak-postgres`, `redis`, `cloudflared`
- **Cloudflare Tunnel** (`cloudflared`) replaces Nginx — outbound-only, no port forwarding, no SSL cert management
  - `app.yourdomain.com` → Next.js (port 3000)
  - `api.yourdomain.com` → FastAPI (port 8000)
  - `auth.yourdomain.com` → Keycloak (port 8080)
- Redis: JWT `jti` blacklist (forced logout), AI event queue
- TLS, WAF, DDoS protection handled at Cloudflare edge — nothing in clinic network exposed directly

---

## Integrations Preserved

| Integration | Current | New Approach |
|---|---|---|
| HL7 v2 lab parsers (27 vendors) | Java HAPI HL7 | Python `hl7apy` — rewritten, same logic |
| FHIR R4 (DHIR immunizations) | Java HAPI FHIR | Python `fhir.resources` — direct |
| OLIS (Ontario lab) | SOAP | FHIR R4 migration in progress at Ontario Health — adopt as available |
| BORN (perinatal registry) | SOAP | FHIR R4 adapter in Python |
| DHIR (immunization registry) | FHIR R4 | Already FHIR R4 — direct |
| MCEDT (Ontario billing) | SOAP | **Temporary:** thin `zeep` Python adapter in isolated container until Ontario REST API available |
| SRFax | Separate Docker container | Unchanged — new backend calls via HTTP |
| ERx (e-prescribing) | Java scheduler | Python scheduled job (APScheduler) — same logic |
| DrugRef2 | Python FastAPI (already!) | Unchanged — new backend calls via HTTP |
| ClinicalConnect | SOAP SSO | SAML federation via Keycloak |
| OneID (Ontario SSO) | Java SAML | SAML federation via Keycloak |

---

## What Is NOT Being Preserved

| Current Component | Reason |
|---|---|
| Struts 1.2.7 | EOL 2013, active CVEs — full replacement |
| 1,817 JSP files | Replaced by Next.js pages |
| Java Hibernate/JPA entities | SQLAlchemy reflects same tables in Python |
| Apache CXF (SOAP/JAX-RS) | Replaced by FastAPI + FHIR R4 |
| AngularJS 1.x SPA | EOL — replaced by Next.js |
| jQuery (7 versions) | Replaced by React |
| Apache Tomcat / Java WAR | Decommissioned at Phase 10 |
| Drools rules engine | Replaced by AI CDS sidecar (with parallel validation period) |
| Spring Integration file jobs | Replaced by Python APScheduler + FastAPI |
| Expedius (long term) | Eventually replaced by S3-compatible object store (MinIO) |

---

## Library Versions (Locked)

```
# Backend
python = "3.12"
fastapi = "0.111"
sqlalchemy = "2.0"
pydantic = "2.7"
fhir-resources = "7.1.0"      # fhir.resources on PyPI
python-jose = "3.3.0"          # JWT validation
python-keycloak = "3.12"       # Keycloak admin API
hl7apy = "1.3.4"               # HL7 v2 parsing
httpx = "0.27"                  # Async HTTP client
apscheduler = "3.10"           # Scheduled jobs
pytest = "8.2"
pytest-asyncio = "0.23"

# Frontend
next = "14.2"
typescript = "5.4"
tailwindcss = "3.4"
@tanstack/react-query = "5.x"
react-hook-form = "7.x"
zod = "3.x"
@fullcalendar/react = "6.x"
@tiptap/react = "2.x"
fhirclient = "2.x"             # SMART on FHIR client

# Auth
keycloak = "24"                 # Docker image

# AI sidecar
anthropic = "0.28"             # Anthropic Python SDK
ollama = "0.2"                 # Ollama Python client
```
