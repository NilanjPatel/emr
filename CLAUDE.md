# OSCAR → Oscar-Next Migration Project

## What This Is

A full technology migration of the OSCAR EMR (Java 8 / Struts / JSP monolith) to a modern stack:
- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.0
- **API standard:** FHIR R4 as primary (replaces all SOAP and custom REST)
- **Frontend:** Next.js 14 App Router + TypeScript + TailwindCSS + shadcn/ui
- **Auth:** Keycloak 24 with SMART on FHIR (self-hosted, Canadian data residency)
- **AI:** FastAPI sidecar + Anthropic Claude API + local Ollama
- **Database:** MariaDB 10.5 — **SCHEMA DOES NOT CHANGE. EVER.**

The old Oscar WAR (Java/Tomcat) runs in parallel throughout migration. We strangle it module by module.

---

## Non-Negotiable Rules

1. **Database schema is frozen.** No ALTER TABLE. No new columns. No new tables unless they are purely for the new system and have zero foreign keys into oscar tables. SQLAlchemy models reflect the existing schema — they do not define it.
2. **FHIR R4 is the API.** No custom REST endpoints for clinical data. Everything that would be a custom endpoint becomes a FHIR resource or FHIR operation. Exception: internal service-to-service calls.
3. **No SOAP.** The only SOAP adapter allowed is a temporary thin `zeep`-based container for MCEDT billing until Ontario provides a REST alternative.
4. **AI is suggestion-only.** No AI output is saved to the database without explicit clinician approval in the UI. No exceptions.
5. **PHIPA/PIPEDA compliance at every step.** Every endpoint that returns patient data must log to `oscar_log` table via the audit middleware. If the audit middleware is not wired, the endpoint does not ship.
6. **Test before moving on.** Each conversion point must pass backend API tests and a frontend golden path test before the next module starts.
7. **Ask before planning.** Do not build implementation plans without user confirmation of the approach first. Discuss, confirm, then plan.

---

## Repository Layout

```
oscar/                          ← existing Oscar Java project (git-tracked, do not modify)
migration/                      ← this directory (NOT git-tracked by oscar project)
├── CLAUDE.md                   ← you are here
├── SKILLS.md                   ← what Claude can do in this project
├── FLOW.md                     ← step-by-step conversion workflow
├── STACK.md                    ← full technology decisions and rationale
├── MODULES.md                  ← conversion status of every Oscar module
├── FHIR.md                     ← FHIR R4 resource mapping for Oscar data model
├── COMPLIANCE.md               ← HIPAA/PIPEDA/PHIPA requirements and checklist
├── progress/                   ← per-module notes as work progresses
└── oscar-next/                 ← the new system (created when Phase 0 starts)
    ├── backend/                ← Python FastAPI FHIR server
    ├── frontend/               ← Next.js 14 app
    ├── ai/                     ← FastAPI AI sidecar
    └── docker/                 ← Docker Compose for new stack
```

---

## Current Phase

**Phase 0 — Foundation** (not started)

See `FLOW.md` for the full phase breakdown and current status.

---

## Source System Quick Reference

| Thing | Where in Oscar |
|---|---|
| Patient (demographic) | `src/main/java/org/oscarehr/common/model/Demographic.java` |
| Appointments | `src/main/java/org/oscarehr/common/model/Appointment.java` |
| Encounter notes | `src/main/java/org/oscarehr/casemgmt/model/CaseManagementNote.java` |
| Prescriptions | `src/main/java/oscar/oscarRx/data/RxPrescriptionData.java` |
| Lab results | `src/main/java/oscar/oscarLab/ca/all/parsers/` (27 handlers) |
| RBAC | `src/main/java/com/quatro/service/security/SecurityManager.java` |
| Audit log | `src/main/java/oscar/log/LogAction.java` → `oscar_log` table |
| Existing REST services | `src/main/java/org/oscarehr/ws/rest/` (36 JAX-RS services) |
| DB schema | `database/mysql/oscarinit.sql` (400+ tables) |

---

## How to Work With Claude in This Project

- Start each session by reading `MODULES.md` to know current status
- Reference `FHIR.md` before designing any new endpoint
- Reference `COMPLIANCE.md` before any patient data endpoint ships
- Do not ask Claude to implement anything without first confirming the approach
- Use `FLOW.md` to know what the next step is
