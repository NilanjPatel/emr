# Phase 0.2 — SQLAlchemy + MariaDB Connection

**Status:** Complete  
**Date:** 2026-06-29  
**Tests:** 9/9 passing (18/18 cumulative)

## What Was Verified

- SQLAlchemy async engine connects to Oscar MariaDB via `aiomysql`
- All core Oscar tables present and readable: `demographic`, `appointment`, `provider`, `casemgmt_note`, `prescription`, `security`, `secRole`, `allergies`, `preventions`
- Zero-date (`0000-00-00`) rows handled without crashing
- Audit log (`log` table) writable — PHIPA compliance gate confirmed

## Key Discoveries (actual DB differs from docs)

| Assumed | Actual | Impact |
|---|---|---|
| Table: `oscar_log` | Table: `log` | Audit middleware updated |
| Table: `Allergy` | Table: `allergies` | FHIR.md + middleware updated |
| `log` columns: action/table/tableId/providerNo/created | `log` columns: dateTime/provider_no/action/content/contentId/ip/data/demographic_no | Audit INSERT updated |

## How to Access DB During Development

MariaDB port is NOT exposed by default. To expose `localhost:3306`:
```bash
cd ~/Documents/ND/oscar
docker compose -f docker-compose.yml -f docker-compose.override.yml up -d db
```
The `docker-compose.override.yml` already has the port mapping — just needs `up -d` (not `restart`).

## Next Step

Phase 0.3 — Audit middleware wired to DB session via FastAPI dependency injection.
Currently the audit middleware writes to `log` table only when `request.state.db` exists.
Need to attach a DB session to each request properly so audit always fires.
