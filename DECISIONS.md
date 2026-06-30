# Architecture Decisions Log

Decisions confirmed with user. Do not revisit without explicit user request.

---

## Decision 001 — Full Rewrite (Path B)
**Date:** 2026-06-29  
**Decision:** Complete rewrite of backend to Python. Java backend is NOT preserved.  
**Rationale:** User confirmed Path B — cleaner, more modern, better AI story. Team comfortable with Python.  
**Implication:** All Java DAOs, entities, managers, and HL7 parsers must be rewritten in Python. Longer timeline but cleaner end result.

---

## Decision 002 — Backend: Python 3.12 + FastAPI
**Date:** 2026-06-29  
**Decision:** FastAPI as the backend framework.  
**Rationale:** Less boilerplate than Spring, async-native, excellent AI/ML ecosystem, easier to hire for, faster iteration.

---

## Decision 003 — No SOAP
**Date:** 2026-06-29  
**Decision:** No SOAP integrations in the new system. Only REST/FHIR R4.  
**Exception:** Temporary thin `zeep`-based MCEDT billing adapter in an isolated container until Ontario Health provides a REST/FHIR alternative.  
**Implication:** OLIS, BORN, DHIR, nCLASS integrations must be converted to their FHIR R4 equivalents as Ontario Health migrates them.

---

## Decision 004 — API Standard: FHIR R4
**Date:** 2026-06-29  
**Decision:** FHIR R4 is the primary API standard. No custom REST endpoints for clinical data.  
**Rationale:** International healthcare interoperability standard. Mandated by Canada Health Infoway and Ontario Health. Enables interoperability with other systems for free.  
**Implication:** All clinical data endpoints are FHIR resources. Internal service-to-service calls may use plain JSON.

---

## Decision 005 — Auth: Keycloak 24 + SMART on FHIR
**Date:** 2026-06-29  
**Decision:** Self-hosted Keycloak with SMART on FHIR profile.  
**Rationale:** PIPEDA/PHIPA Canadian data residency requirement rules out Auth0/Cognito. SMART on FHIR is the OAuth 2.0 profile designed for healthcare.  
**Implication:** Keycloak runs in the clinic's Docker stack. AWS ca-central-1 or OCI Toronto for cloud deployments.

---

## Decision 006 — Database Schema Frozen
**Date:** 2026-06-29  
**Decision:** MariaDB 10.5 schema does not change. No ALTER TABLE. No new columns in existing tables.  
**Rationale:** User hard requirement. Data integrity and continuity with the running Oscar WAR.  
**Implication:** SQLAlchemy models use reflection (`autoload_with`). New-system-only data goes in `oscar_next` schema.

---

## Decision 007 — Frontend: Next.js 14 App Router + TypeScript
**Date:** 2026-06-29  
**Decision:** Next.js 14 with App Router, TypeScript, TailwindCSS, shadcn/ui.  
**Rationale:** Modern, professional, maintainable. Server Components for initial render (clinic bandwidth). React ecosystem for complex clinical UI.

---

## Decision 008 — AI is Suggestion-Only
**Date:** 2026-06-29  
**Decision:** No AI output is persisted to the database without explicit clinician approval.  
**Rationale:** Health Canada digital health guidance. Clinical safety. Regulatory requirement.  
**Implication:** Every AI endpoint returns suggestions. The UI must show a clear "Accept" action. Auto-save of AI content is prohibited.

---

## Decision 009 — AI PHI: On-Premise for Real-Time
**Date:** 2026-06-29  
**Decision:** Real-time AI features (encounter assist, ambient charting) use on-premise Ollama. External Anthropic API only for async tasks after de-identification.  
**Rationale:** PIPEDA data residency. PHI must not leave the clinic network for real-time processing.

---

## Decision 010 — Full Cutover (Not Strangler Fig)
**Date:** 2026-06-29  
**Decision:** Oscar WAR is NOT running side-by-side. New system replaces it directly. No Nginx traffic splitting.  
**Rationale:** User confirmed no need for dual-running. Test database is available. Clean cutover per module is simpler.  
**Implication:** Each module is built and tested against the real Oscar DB, then deployed as the sole system for that function.

---

## Decision 011 — Cloudflare Tunnel (No Nginx)
**Date:** 2026-06-29  
**Decision:** Cloudflare Tunnel (`cloudflared`) replaces Nginx as the ingress layer. User has Cloudflare account and domain.  
**Rationale:** No port forwarding required. Outbound-only tunnel — more secure for clinic network. Free TLS, DDoS protection, and WAF at Cloudflare edge. No SSL cert management.  
**Implication:** `cloudflared` container added to Docker Compose. Routes:
- `app.yourdomain.com` → Next.js frontend (port 3000)
- `api.yourdomain.com` → FastAPI backend (port 8000)
- `auth.yourdomain.com` → Keycloak (port 8080)

All internal — nothing exposed to internet except through the tunnel.

---

## Open Questions (Not Yet Decided)

| Question | Context | Status |
|---|---|---|
| Team size? | Affects phase timeline | Not asked |
| Target deployment: single-clinic Docker or multi-clinic cloud? | Affects infrastructure decisions — Cloudflare Tunnel confirmed, domain exists | Partially resolved |
| BC billing priority vs Ontario? | Affects Phase 6 scope | Not asked |
| Expedius (document management) — replace or keep? | MinIO vs Expedius container | Not asked |
| EMR name for the new system? | For project directory naming | Not asked |
