# Module Conversion Status

## Status Legend
- `not-started` — not yet discussed
- `in-discussion` — being discussed with user
- `confirmed` — user approved approach, ready to build
- `building` — currently being converted
- `testing` — built, in test phase
- `converted` — fully done, tests passing, Nginx routed to new system
- `blocked` — blocked by dependency or decision needed

---

## Priority Order (Phase by Phase)

### Phase 0 — Foundation Infrastructure

| Component | Status | Notes |
|---|---|---|
| Python FastAPI project scaffold | `converted` | Done 2026-06-29 — 9/9 tests passing |
| SQLAlchemy + MariaDB connection (read-only verify) | `converted` | Done 2026-06-29 — 9/9 tests passing. log table=`log`, allergy table=`allergies` |
| Audit middleware → `oscar_log` | `converted` | Done 2026-06-29 — DB session middleware wired, audit fires end-to-end into `log` table |
| Keycloak + SMART on FHIR | `converted` | Done 2026-06-29 — PostgreSQL backend, oscar realm imported, SMART on FHIR scopes configured, 4/4 tests passing |
| JWT validation middleware | `converted` | Done 2026-06-29 — RS256 validation, JWKS cache with TTL+rotation, roles on request.state, 10/10 tests passing |
| RBAC middleware (`secRole`/`secObjPrivilege`) | `converted` | Done 2026-06-29 — privilege matrix from live DB, require_permission() dependency, 24/24 tests passing |
| Next.js project scaffold + Keycloak OIDC | `converted` | Done 2026-06-29 — Next.js 14, NextAuth/Keycloak, clinic shell layout, ⌘K command palette, F1-F7 shortcuts, clean build |
| ~~Nginx config~~ → Cloudflare Tunnel | `skipped` | Decision 2026-06-29 — No Nginx, no side-by-side WAR. Cloudflare Tunnel routes domain traffic to new services directly. Config added to Docker Compose in Phase 0.9 |
| Docker Compose extended | `converted` | Done 2026-06-29 — all services wired: keycloak, postgres, oscar-api, oscar-web, oscar-ai, redis, cloudflared |
| AI sidecar scaffold | `converted` | Done 2026-06-29 — FastAPI, de-identification pipeline (18 HIPAA identifiers), Ollama + Anthropic clients, 4 routers, 24/24 tests passing |

### Phase 1 — Schedule + Appointments

| Module | Status | FHIR Resource | Oscar Tables | Source Reference |
|---|---|---|---|---|
| Provider schedule templates | `not-started` | `Schedule` | `rschedule`, `scheduletemplate` | `ScheduleService.java` |
| Available slots | `not-started` | `Slot` | `scheduledate`, `scheduletemplatecode` | `ScheduleService.java` |
| Appointment booking | `not-started` | `Appointment` | `appointment` | `ScheduleService.java` |
| Appointment types | `not-started` | `Appointment.serviceType` | `appointmentType` | |
| Wait list | `not-started` | `Appointment` (status=waitlist) | `oscarWaitingList` | |

### Phase 2 — Patient Demographics

| Module | Status | FHIR Resource | Oscar Tables | Source Reference |
|---|---|---|---|---|
| Patient search | `not-started` | `Patient` (search) | `demographic` | `DemographicService.java` |
| Patient profile (view/edit) | `not-started` | `Patient` | `demographic`, `demographicExt` | `DemographicService.java` |
| Patient contacts | `not-started` | `RelatedPerson` | `DemographicContact` | |
| Patient merge | `not-started` | FHIR `$merge` operation | `demographicMerged` | `DemographicMergeService.java` |
| Consent | `not-started` | `Consent` | `Consent`, `consentType` | `ConsentService.java` |

### Phase 3 — Encounter Notes + CPP

| Module | Status | FHIR Resource | Oscar Tables | Source Reference |
|---|---|---|---|---|
| Encounter note (SOAP) | `not-started` | `Encounter`, `Composition` | `casemgmt_note` | `NotesService.java` |
| Active problems list | `not-started` | `Condition` | `casemgmt_issue`, `Dxresearch` | |
| Allergies | `not-started` | `AllergyIntolerance` | `Allergy` | `AllergyService.java` |
| Family history | `not-started` | `FamilyMemberHistory` | `casemgmt_note` (type) | |
| Social history | `not-started` | `Observation` | `casemgmt_note` (type) | |
| Measurements / vitals | `not-started` | `Observation` | `measurements` | `MeasurementService.java` |
| Flowsheets | `not-started` | `Observation` (bundle) | `Flowsheet` | |
| Ticklers / tasks | `not-started` | `Task` | `tickler` | `TicklerWebService.java` |
| AI encounter assist | `not-started` | n/a (AI sidecar) | writes to `casemgmt_note` on approval | |

### Phase 4 — Prescriptions

| Module | Status | FHIR Resource | Oscar Tables | Source Reference |
|---|---|---|---|---|
| Active medications | `not-started` | `MedicationRequest` | `prescription`, `prescribe` | `RxWebService.java` |
| Drug search | `not-started` | `Medication` | `drugref2` DB | DrugRef2 API |
| Prescription print/fax | `not-started` | `MedicationRequest` + document | | |
| ERx integration | `not-started` | `MedicationRequest` | `prescription` | `ERxScheduler.java` |
| Drug interactions | `not-started` | n/a (AI sidecar augments DrugRef2) | | |

### Phase 5 — Lab Results

| Module | Status | FHIR Resource | Oscar Tables | Source Reference |
|---|---|---|---|---|
| Lab result display | `not-started` | `DiagnosticReport`, `Observation` | `labTestResults` | `LabService.java` |
| HL7 v2 lab ingest (27 parsers) | `not-started` | `DiagnosticReport` | `labTestResults`, `patientLabRouting` | `oscar/oscarLab/ca/all/parsers/` |
| OLIS integration | `not-started` | FHIR R4 (Ontario Health) | `OLISResults` | |
| Lab routing | `not-started` | `DiagnosticReport.performer` | `providerLabRouting` | |

### Phase 6 — Billing

| Module | Status | FHIR Resource | Oscar Tables | Source Reference |
|---|---|---|---|---|
| Billing entry (Ontario OHIP) | `not-started` | `Claim` | `billing`, `billingdetail` | `BillingService.java` |
| MCEDT submission | `not-started` | via zeep adapter | `billing_on_payment` | MCEDT adapter |
| Billing reconciliation | `not-started` | `ClaimResponse` | `raheader`, `radetail` | |
| BC billing | `not-started` | `Claim` | `billing` (BC variant) | |
| AI billing code suggestion | `not-started` | n/a (AI sidecar) | | |

### Phase 7 — Documents + Inbox

| Module | Status | FHIR Resource | Oscar Tables | Source Reference |
|---|---|---|---|---|
| Document management (DMS) | `not-started` | `DocumentReference` | `document` | `DocumentService.java` |
| Hospital reports (HRM) | `not-started` | `DocumentReference` | `HRMDocument` | |
| Provider inbox | `not-started` | `Communication` | `providerLabRouting` (inbox) | `InboxService.java` |
| Internal messaging | `not-started` | `Communication` | `messagelisttbl` | `MessagingService.java` |
| Fax (SRFax) | `not-started` | `DocumentReference` | via faxws container | |

### Phase 8 — Preventions + Immunizations

| Module | Status | FHIR Resource | Oscar Tables | Source Reference |
|---|---|---|---|---|
| Immunization record | `not-started` | `Immunization` | `preventions`, `preventionsExt` | `PreventionService.java` |
| Immunization recommendations | `not-started` | `ImmunizationRecommendation` | | |
| DHIR submission | `not-started` | FHIR R4 (already) | `DHIRSubmissionLog` | |
| Screening reminders | `not-started` | `ImmunizationRecommendation` | | |

### Phase 9 — Admin + Reporting

| Module | Status | FHIR Resource | Oscar Tables | Source Reference |
|---|---|---|---|---|
| User management | `not-started` | Keycloak Admin API | `security`, `secRole` | |
| Role management | `not-started` | Keycloak Admin API | `secObjPrivilege` | |
| Provider management | `not-started` | `Practitioner` | `provider`, `providerExt` | `ProviderService.java` |
| Reports / dashboards | `not-started` | `MeasureReport` | various | `ReportingService.java` |
| eForms | `not-started` | `Questionnaire`, `QuestionnaireResponse` | `EFormDocs` | `FormsService.java` |
| Consultations / referrals | `not-started` | `ServiceRequest` | `consultations` tables | `ConsultationWebService.java` |
| Surveillance | `not-started` | `MeasureReport` | | `SurveillanceService.java` |

### Phase 10 — Decommission

| Task | Status | Notes |
|---|---|---|
| Remove Oscar WAR from Docker Compose | `not-started` | Only when ALL modules converted and tested |
| Archive Java codebase | `not-started` | |
| Remove Tomcat container | `not-started` | |

---

## Dependency Map

```
Phase 0 (Foundation)
    └── Phase 1 (Schedule)
            └── Phase 2 (Demographics)
                    ├── Phase 3 (Encounters) ← AI goes live here
                    │       └── Phase 4 (Prescriptions)
                    │               └── Phase 5 (Labs)
                    │                       └── Phase 6 (Billing)
                    └── Phase 7 (Documents) ← parallel with 3+
                    └── Phase 8 (Preventions) ← parallel with 4+
                    └── Phase 9 (Admin) ← parallel with 5+
```

Phase 10 depends on ALL phases complete.

---

## Conversion Stats

| Status | Count |
|---|---|
| converted | 9 |
| testing | 0 |
| building | 0 |
| confirmed | 0 |
| in-discussion | 0 |
| not-started | 50 |
| blocked | 0 |

*Last updated: 2026-06-29*
