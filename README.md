# Oscar → Oscar-Next Migration

This directory contains all planning, context, and working files for the OSCAR EMR technology migration.

**This directory is outside the oscar git repository and is not tracked by version control.**

## Files

| File | Purpose |
|---|---|
| `CLAUDE.md` | Primary context file — read this first in every session |
| `FLOW.md` | Step-by-step conversion workflow and phase status |
| `MODULES.md` | Status of every Oscar module (not-started → converted) |
| `STACK.md` | Full technology stack decisions and library versions |
| `FHIR.md` | FHIR R4 resource mappings for every Oscar data model |
| `COMPLIANCE.md` | HIPAA/PIPEDA/PHIPA requirements and checklist |
| `DECISIONS.md` | Architecture decisions log — confirmed choices with rationale |
| `SKILLS.md` | How Claude should behave and what it can do in this project |
| `UX.md` | UX design reference — keyboard shortcuts, wireframes, Accuro/Jane competitor analysis |
| `progress/` | Per-module notes created as work progresses |
| `oscar-next/` | The new system code (created when Phase 0 starts) |

## How to Start a Session

Tell Claude:
> "Read CLAUDE.md and MODULES.md in /Users/bcdhawan/Documents/ND/oscar/migration/ and tell me where we are and what the next step is."

## Stack Summary

- **Backend:** Python 3.12 + FastAPI + SQLAlchemy 2.0
- **API:** FHIR R4 (replaces all SOAP and custom REST)
- **Frontend:** Next.js 14 + TypeScript + TailwindCSS + shadcn/ui
- **Auth:** Keycloak 24 + SMART on FHIR
- **AI:** FastAPI sidecar + Anthropic Claude + local Ollama
- **Database:** MariaDB 10.5 — **schema unchanged**

## Current Phase

Phase 0 — Foundation (not started)
