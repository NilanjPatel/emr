# Phase 0.3 — DB Session Middleware

**Status:** Complete  
**Date:** 2026-06-29  
**Tests:** 6/6 passing (24/24 cumulative)

## What Was Built

`app/middleware/db_session.py` — opens an AsyncSession at request start,
attaches it to `request.state.db`, closes cleanly after response.

## Middleware Stack (order matters in Starlette)

Starlette adds middleware in reverse — last `add_middleware` runs first on the request.

```
Request in:   DBSessionMiddleware → AuditMiddleware → [AuthMiddleware Phase 0.5] → route
Response out: route → [AuthMiddleware] → AuditMiddleware → DBSessionMiddleware
```

DBSessionMiddleware runs first so `request.state.db` is available to everything downstream.

## Key Discovery

`provider_no` column in `log` table is `varchar(10)` — usernames longer than 10 chars
get silently truncated by MariaDB. Keycloak usernames must be kept ≤ 10 chars,
or we store the provider_no (numeric) not the username string.
→ Will use `provider_no` (numeric ID from secRole) not username once RBAC is wired in Phase 0.6.

## Next Step

Phase 0.4 — Keycloak container setup + SMART on FHIR configuration.
