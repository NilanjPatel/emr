# Conversion Flow — Step by Step

## The Golden Rule of This Migration

```
DISCUSS → CONFIRM → BUILD → TEST BACKEND → TEST FRONTEND → MARK DONE → NEXT
```

Never skip a step. Never start the next module until the current one passes tests.

---

## Conversion Point Workflow (Per Module)

```
1. IDENTIFY
   Claude reads MODULES.md, identifies the next unconverted module
   Claude reads the Oscar source files for that module
   Claude summarizes: what does this module do, what DB tables does it touch,
   what FHIR resource(s) does it map to, what are the edge cases

2. DISCUSS FUNCTIONALITY
   Claude presents the conversion approach as a discussion, NOT a plan
   User asks questions, pushes back, refines
   Key questions: FHIR resource mapping correct? Any integrations to preserve?
   Any compliance considerations?

2b. DISCUSS UX/DESIGN (physician-primary screens only: schedule, encounter, patient chart)
   Claude proposes text wireframe layout
   Claude proposes keyboard shortcuts for this screen
   Claude references how Accuro/Jane/Epic handle this workflow
   User reviews and adjusts
   For all other screens: skip this step, apply standard design patterns

3. CONFIRM
   User explicitly says "go ahead" or "approved" or similar
   Only then does Claude proceed

4. BUILD BACKEND
   - SQLAlchemy model reflecting existing MariaDB table (no schema change)
   - Pydantic/FHIR resource model
   - FastAPI FHIR endpoint(s)
   - Audit middleware wired
   - Unit tests

5. TEST BACKEND
   - Run pytest against the new endpoints
   - Verify FHIR resource validates against fhir.resources schema
   - Verify audit log entry created for every patient data access
   - Verify existing Oscar WAR still works (no regression)
   Only pass this step when all tests green

6. BUILD FRONTEND
   - Next.js page/component for this module
   - Consumes the new FHIR endpoint
   - Matches the golden path workflow

7. TEST FRONTEND
   - Manual golden path test: describe what was done and what the result was
   - Verify the Keycloak auth gate works
   - Verify no console errors
   Only pass when golden path confirmed working

8. MARK DONE
   Update MODULES.md: status → converted, date, notes
   Update COMPLIANCE.md if new compliance items were addressed

9. NEXT
   Move to next module in MODULES.md priority order
```

---

## Phases

### Phase 0 — Foundation
**Status:** Not started

**Goal:** The pipes. Nothing visible to clinicians changes.

Steps (confirm each with user before starting):
- [ ] 0.1 — Scaffold `oscar-next/backend/` Python project (FastAPI, SQLAlchemy, alembic config read-only)
- [ ] 0.2 — Connect SQLAlchemy to existing MariaDB (read-only first, verify models reflect tables)
- [ ] 0.3 — Implement audit middleware (writes to `oscar_log` table on every patient data request)
- [ ] 0.4 — Implement Keycloak container + SMART on FHIR configuration
- [ ] 0.5 — JWT validation middleware in FastAPI (validates Keycloak RS256 tokens)
- [ ] 0.6 — RBAC middleware (reads `secRole`/`secObjPrivilege` tables, enforces per-endpoint)
- [ ] 0.7 — Scaffold `oscar-next/frontend/` Next.js project with Keycloak OIDC and clinic shell
- [ ] 0.8 — Nginx config routing `/fhir/` → new backend, `/oscar/` → old WAR
- [ ] 0.9 — Docker Compose extended with new services alongside existing ones
- [ ] 0.10 — Scaffold `oscar-next/ai/` FastAPI sidecar (stubbed endpoints, no LLM yet)

**Gate:** Old Oscar WAR must still be fully functional after Phase 0. Zero clinical impact.

---

### Phase 1 — Schedule + Appointments
**Status:** Not started  
**Depends on:** Phase 0 complete  
**FHIR resources:** `Schedule`, `Slot`, `Appointment`  
**Oscar tables:** `appointment`, `rschedule`, `scheduledate`, `scheduletemplate`  
**Oscar source:** `org.oscarehr.ws.rest.ScheduleService` (reference implementation)

---

### Phase 2 — Patient Demographics
**Status:** Not started  
**Depends on:** Phase 1 complete  
**FHIR resources:** `Patient`, `RelatedPerson`  
**Oscar tables:** `demographic`, `demographicExt`, `DemographicContact`  
**Oscar source:** `org.oscarehr.ws.rest.DemographicService`  
**Note:** This is the FK root — every other clinical resource links here. Get it right.

---

### Phase 3 — Encounter Notes + CPP
**Status:** Not started  
**Depends on:** Phase 2 complete  
**FHIR resources:** `Encounter`, `Composition`, `Condition`, `AllergyIntolerance`, `FamilyMemberHistory`  
**Oscar tables:** `casemgmt_note`, `casemgmt_issue`, `encounter`  
**Note:** AI encounter assist goes live here (suggestion-only). Hardest module.

---

### Phase 4 — Prescriptions
**Status:** Not started  
**Depends on:** Phase 3 complete  
**FHIR resources:** `MedicationRequest`, `Medication`  
**Oscar tables:** `prescription`, `prescribe`, `drugs`  
**Integrations:** DrugRef2 (already Python/FastAPI — wire directly)

---

### Phase 5 — Lab Results
**Status:** Not started  
**Depends on:** Phase 4 complete  
**FHIR resources:** `DiagnosticReport`, `Observation`  
**Oscar tables:** `labTestResults`, `patientLabRouting`  
**Note:** 27 HL7 v2 lab parsers must be rewritten in Python. Regression test suite required first.

---

### Phase 6 — Billing
**Status:** Not started  
**Depends on:** Phase 5 complete  
**FHIR resources:** `Claim`, `ClaimResponse`, `Coverage`  
**Oscar tables:** `billing`, `billingdetail`, `billing_on_payment`  
**Note:** MCEDT SOAP adapter (thin zeep container) stays until Ontario provides REST/FHIR.

---

### Phase 7 — Documents + Inbox
**Status:** Not started  
**Depends on:** Phase 2 complete (parallel with Phase 3+)  
**FHIR resources:** `DocumentReference`, `Communication`  
**Oscar tables:** `document`, `HRMDocument`

---

### Phase 8 — Preventions / Immunizations
**Status:** Not started  
**FHIR resources:** `Immunization`, `ImmunizationRecommendation`  
**Oscar tables:** `preventions`, `preventionsExt`  
**Integrations:** DHIR R4 (already FHIR — straightforward)

---

### Phase 9 — Admin + User Management
**Status:** Not started  
**Note:** Mostly Keycloak configuration. User/role sync from `security`/`secRole` tables.

---

### Phase 10 — Decommission Oscar WAR
**Status:** Not started  
**Depends on:** All phases complete and verified  
**Action:** Remove Tomcat container from Docker Compose. Archive the Java codebase.

---

## Testing Standards

### Backend Test (must pass before frontend work starts)
```bash
# From oscar-next/backend/
pytest tests/test_<module>.py -v
# All tests green
# FHIR resource validation passes
# Audit log entry verified in oscar_log table
```

### Frontend Test (must pass before marking module done)
Golden path documented in `progress/<module>.md`:
- Login as test provider
- Navigate to module
- Perform the primary workflow (book appointment / view patient / write note / etc.)
- Confirm data saved correctly in MariaDB
- Confirm audit log entry created
- No console errors

---

## Rollback Plan (Per Module)

Each module cutover is controlled by Nginx routing. To roll back any module:
1. Edit `nginx/default.conf` — point route back to `/oscar/` WAR
2. Reload Nginx: `docker exec nginx nginx -s reload`
3. No data loss — both systems write to the same MariaDB

---

## Definition of Done (Per Module)

- [ ] SQLAlchemy model matches existing MariaDB table (verified with `SELECT *` spot check)
- [ ] FHIR R4 endpoint returns valid FHIR JSON (validated by `fhir.resources`)
- [ ] All patient data access logs to `oscar_log` table
- [ ] Keycloak auth enforced (401 without valid token)
- [ ] RBAC enforced (403 for insufficient role)
- [ ] pytest suite passes
- [ ] Frontend golden path passes
- [ ] `MODULES.md` updated to `converted`
- [ ] Old Oscar WAR still functional (no regression introduced)
