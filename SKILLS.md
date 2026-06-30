# Claude Skills for This Project

## UX Design Mandate

This system must be better than Accuro EMR — the current Canadian market leader (71% physician satisfaction vs OSCAR's 63%). Key benchmarks:

**Accuro's keyboard shortcuts to match/beat:**
- `F1` Patient search, `F3` Quick patient summary, `F4` Appointments, `F5` Documents, `F9` Chart
- `F12` Date/time stamp in notes
- Full section navigation via keyboard

**AI standard to meet:** Accuro AI Scribe (Heidi-powered) — embedded in encounter note, single-click push to chart, pre-visit questionnaires, generates SOAP + referral + patient summary from one visit. Our system must do this or better, using Anthropic Claude + Ollama.

**Jane App lesson:** 4.8/5 from 5,500+ reviews because staff pick it up without training. Every screen we build must be self-evident to a physician who has never seen it.

**Design-as-you-build rule:**
- For physician-primary screens (schedule, encounter note, patient chart): always do a design discussion with text wireframe + keyboard shortcut map BEFORE writing any code
- For all other screens: apply consistent design patterns and build — no separate design pass needed
- Reference Accuro/Jane/Epic patterns when proposing any layout

---

## What Claude Should Always Do

### Before Any Conversation
1. Read `MODULES.md` — understand current phase and status
2. Read `FLOW.md` — know what the next step is
3. Read `COMPLIANCE.md` — know current compliance posture

### During Any Conversation
- **Discuss, don't plan.** When a new module or approach comes up, explain and discuss it. Do not produce an implementation plan without user confirmation.
- **Reference the source.** Always look at the actual Oscar Java source file for the module being converted — it is the spec. Never guess what Oscar does.
- **FHIR first.** Before designing any endpoint, check `FHIR.md` for the correct resource mapping. Don't invent custom resources.
- **Audit always.** Every new endpoint touching patient data must wire the audit middleware. This is not optional and not skippable.
- **State the next step.** After completing any step, say: "Step X done. Next step is Y — should I proceed?"

### When Writing Code
- SQLAlchemy models: use `autoload_with=engine` to reflect existing tables. Never define columns that would imply schema changes.
- FastAPI endpoints: FHIR resource in, FHIR resource out. Validate with `fhir.resources` before returning.
- Next.js pages: use `react-query` for data fetching. Use `react-hook-form` + `zod` for forms. No `useEffect` + `fetch` patterns.
- Tests: write pytest for backend before writing any frontend code for that module.

---

## What Claude Should Never Do

- Create implementation plans without user confirmation
- Suggest changing the MariaDB schema (no ALTER TABLE, no new columns in existing tables)
- Design custom REST endpoints for clinical data (use FHIR R4 resources)
- Add SOAP integrations (temporary MCEDT adapter is the only exception)
- Skip the audit middleware on any endpoint returning patient data
- Save AI suggestions to the database without explicit clinician approval in the UI
- Move to the next module before the current one has passing tests
- Assume what Oscar does — always read the source

---

## Standard Commands for This Project

### Check current status
```
Read MODULES.md → tell me current phase and next step
```

### Start a new module discussion
```
Read MODULES.md → identify next module → read Oscar source files for that module →
summarize: what it does, what tables, what FHIR resource → present to user for discussion
```

### Build a module (after user confirmation)
```
1. Write SQLAlchemy model (reflect existing table)
2. Write Pydantic/FHIR schema
3. Write FastAPI FHIR endpoint with audit middleware
4. Write pytest tests
5. Report: "Backend built. Run: pytest tests/test_<module>.py"
6. Wait for test confirmation before starting frontend
7. Write Next.js page/component
8. Report: "Frontend built. Golden path test: [describe steps]"
9. Wait for frontend test confirmation
10. Update MODULES.md
```

### When stuck on FHIR mapping
```
Read FHIR.md → if not there, search fhir.resources docs or HL7 FHIR R4 spec →
propose mapping to user → confirm before implementing
```

### When a compliance question comes up
```
Read COMPLIANCE.md → check if addressed → if not, flag to user before proceeding
```

---

## Token Efficiency Rules

To avoid wasting tokens:

1. **Don't re-read files you just read** in the same session unless something changed
2. **Don't explain Oscar's old code** unless the user asks — just extract what's needed for the new implementation
3. **Don't summarize what you just did** at the end of every response — the user can see the output
4. **One question at a time** — if you need clarification, ask the single most important question, not a list of 5
5. **Reference files by path, don't quote them** — say "see `MODULES.md` line 42" not paste the whole file
6. **Short code, long tests** — write minimal implementation code, comprehensive test code

---

## Project-Specific Knowledge

### The Key Seam
The existing Oscar AngularJS SPA (`src/main/webapp/web/`) already calls JAX-RS REST services at `/oscar/ws/rs/`. This proves the pattern works. The new system follows the same seam but with FHIR R4 resources instead of custom JSON.

### The Hardest Module
Encounter notes (`casemgmt_note` table). It has no clean schema — it stores structured and unstructured data mixed together, with type flags that determine meaning. Read `CaseManagementNote.java` carefully before Phase 3.

### The Most Dangerous Module
Lab results. Wrong lab attached to wrong patient is a clinical safety event. The 27 HL7 parser regression test suite must be built and passing before any lab code ships.

### The Most Complex Integration
MCEDT (Ontario billing submission). It is SOAP-only, certified with Ontario Health. The zeep adapter is a wrapper — it should not contain any billing business logic, only protocol translation. All billing logic stays in FastAPI.

### Database Quirks to Know
- `zeroDateTimeBehavior=round` — Oscar has zero dates (`0000-00-00`) in many timestamp fields. SQLAlchemy must handle these without crashing. Use `NULLTYPE` mapping or custom type.
- `demographic.demographic_no` — the patient primary key. It is called `demographic_no` not `id` or `patient_id`.
- `appointment.status` — single character code, not a readable string. Map these in `FHIR.md`.
- Many tables have `lastUpdateDate` and `lastUpdateUser` — these are audit fields Oscar maintains. The new system must continue writing them correctly.
