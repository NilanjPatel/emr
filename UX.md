# UX Design Reference

## Target: Better Than Accuro

Accuro EMR is the Canadian market leader (71% physician satisfaction, Doctors of BC 2022).
OSCAR currently sits at 63%. Our target is 85%+.
Jane App sits at 4.8/5 from 5,500+ reviews — achieved purely through clean, learnable UX.

**The bar:** A physician who has never seen this system should be able to book an appointment,
open a patient chart, and write an encounter note within 5 minutes — without reading a manual.

---

## Global Keyboard Shortcuts (System-Wide)

To be implemented in the Next.js clinic shell. Inspired by Accuro + modern productivity apps.

| Shortcut | Action | Priority |
|---|---|---|
| `⌘K` / `Ctrl+K` | Command palette — search patients, actions, navigation | P0 — build in Phase 0 shell |
| `F1` | Patient search | P0 |
| `F3` | Quick patient summary (hover panel) | Phase 2 |
| `F4` | Patient appointments view | Phase 1 |
| `F5` | Documents / inbox | Phase 7 |
| `F9` | Open chart / encounter | Phase 3 |
| `F12` | Insert date/time stamp at cursor (in notes) | Phase 3 |
| `Escape` | Close modal / panel | P0 |
| `N` (schedule view) | New appointment | Phase 1 |
| `T` (schedule view) | Jump to today | Phase 1 |
| `←` / `→` (schedule view) | Previous / next day | Phase 1 |
| `Ctrl+S` / `⌘S` | Save current form / note | All phases |
| `Ctrl+Enter` | Sign / finalize encounter note | Phase 3 |
| `?` | Show keyboard shortcut help overlay | Phase 0 shell |

**Command palette (`⌘K`)** is the single most important UX feature:
- Search patients by name, HIN, DOB, phone
- Search actions ("new appointment", "write prescription", "view labs")
- Navigate to any module
- Works from anywhere in the app
- Implemented with `cmdk` library in Next.js

---

## Physician-Primary Screens — Design Principles

### 1. Schedule / Appointment Calendar

**Accuro pattern:** Day/week grid, provider switcher, quick-book from empty slot, patient name + reason visible inline.

**Our approach:**
```
┌─────────────────────────────────────────────────────────────┐
│  ← Mon Jun 29 →   [Today]   Dr. Smith ▾   [+ New Appt]  ⌘K │
├──────┬──────────────────────────────────────────────────────┤
│ 8:00 │ ▓▓▓ John Doe · Annual physical · Room 2             │
│ 8:15 │     [click to book]                                  │
│ 8:30 │ ▓▓▓ Jane Smith · Follow-up HTN · Arrived ✓         │
│ 8:45 │ ▓▓▓ (cont.)                                          │
│ 9:00 │     [click to book]                                  │
│ 9:15 │ ▓▓▓ BLOCKED — lunch                                  │
└──────┴──────────────────────────────────────────────────────┘
Shortcuts: N=new  F=find patient  T=today  ←/→=day  ?=help
```

**Key decisions:**
- Status badge inline: Booked / Arrived / In Room / Billed / No-Show — color coded
- Hover on appointment: shows patient DOB, HIN, phone, last visit — no click needed
- Right-click context menu: Check in / Cancel / Reschedule / Open Chart
- Multi-provider view: tab per provider, not a separate page

### 2. Patient Chart (Summary View)

**Accuro pattern:** Always-visible patient banner, CPP (problems/meds/allergies) on left, encounter history on right, single-click to open any encounter.

**Our approach:**
```
┌─────────────────────────────────────────────────────────────┐
│ JOHN DOE  DOB: 1965-03-14 (61M)  HIN: 1234-567-890  ⚠ Allergies: Penicillin │
│ Dr. Smith · Last visit: Jun 15, 2026 · [Book Appt] [New Encounter] [Rx] │
├────────────────────┬────────────────────────────────────────┤
│ ACTIVE PROBLEMS    │ RECENT ENCOUNTERS                       │
│ • Hypertension     │ Jun 15 — Follow-up HTN (Dr. Smith)    │
│ • T2DM             │ Mar 02 — Annual physical               │
│ • Osteoarthritis   │ Jan 10 — Rx renewal                   │
│                    │                                         │
│ MEDICATIONS        │ LABS (latest)                          │
│ • Metformin 500mg  │ A1C: 7.2% ↑  Jun 1                   │
│ • Ramipril 10mg    │ Creatinine: 88  Jun 1                 │
│                    │                                         │
│ ALLERGIES          │ PREVENTIONS DUE                        │
│ • Penicillin (hives│ ⚠ Flu vaccine — overdue               │
└────────────────────┴────────────────────────────────────────┘
```

**Key decisions:**
- Patient banner is always visible (sticky) when chart is open — never scrolls away
- Abnormal lab values flagged with ↑/↓ and color
- Overdue preventions surfaced directly on chart summary — AI-driven
- CPP (left panel) is always visible alongside encounter list

### 3. Encounter Note Editor

**Accuro AI Scribe pattern:** AI embedded in note, single-click to accept, generates SOAP + referral + patient summary from one visit.

**Our approach:**
```
┌─────────────────────────────────────────────────────────────┐
│ Encounter — John Doe — Jun 29, 2026 · Dr. Smith    [Sign ⌘↩]│
├─────────────────────────────────┬───────────────────────────┤
│ SOAP NOTE                       │ AI ASSIST          ✦      │
│                                 │ ─────────────────────────│
│ S: Patient presents with...     │ Suggested additions:      │
│                                 │                           │
│ O: BP 138/82  HR 72             │ "Consider A1C recheck     │
│    Wt 84kg  BMI 28.4            │  given last result 7.2%   │
│                                 │  (3 months ago)"          │
│ A: HTN — controlled             │                           │
│    T2DM — suboptimal control    │ [Accept] [Dismiss]        │
│                                 │ ─────────────────────────│
│ P: Continue Metformin...        │ Billing suggestion:       │
│                                 │ A001 + K030              │
│ [F12 = timestamp]               │ [Accept] [Dismiss]        │
└─────────────────────────────────┴───────────────────────────┘
🎤 [Start ambient recording]   Generating from audio...
```

**Key decisions:**
- AI panel is a sidebar, not a popup — always visible while typing
- AI suggestions require explicit Accept — never auto-inserted
- Ambient recording button visible but not required
- Billing codes suggested from note text — physician accepts or overrides
- `Ctrl+Enter` / `⌘↩` to sign and close encounter
- `F12` inserts current date/time at cursor

---

## Global Design System Rules

These apply to every screen we build:

1. **Color:** Clinical neutral — white/light gray background, one accent color (deep blue or teal). No bright colors except for alerts (red = critical, amber = warning, green = normal).

2. **Typography:** Inter or Geist (Next.js default) — clean, high legibility at small sizes. Physicians read a lot of text.

3. **Density:** Medium density — not cramped like OSCAR, not spacious like a consumer app. Physicians need to see a lot of information at once.

4. **Alerts surface automatically:** Abnormal labs, overdue preventions, drug interactions — shown inline, not in a separate alerts screen.

5. **No dead ends:** Every screen has a clear next action. If a patient chart is open, "New Encounter" and "Book Appointment" are always one click away.

6. **Mobile-aware but desktop-first:** Physicians chart on desktops. Nurses check on tablets. Responsive but optimized for 1280px+ width.

7. **Loading states always visible:** Clinical data can be slow. Every data fetch shows a skeleton loader, never a blank screen.

8. **Error messages are human:** "Could not save the encounter note — please try again" not "500 Internal Server Error".

---

## Competitor Reference

| Feature | Accuro | Jane App | OSCAR | Our Target |
|---|---|---|---|---|
| Keyboard shortcuts | Full (F1-F12, Ctrl) | Limited | Minimal | Full + ⌘K palette |
| AI charting | Yes (Heidi/AI Scribe) | No | No | Yes (Claude + Ollama) |
| Mobile access | Yes | Yes | Limited | Yes (responsive) |
| Patient portal | Yes | Yes | MyOSCAR (basic) | Phase TBD |
| Pre-visit intake | Yes (AI questionnaire) | Yes | No | Phase 3 (AI) |
| Setup time | Days | Hours | Weeks | Hours |
| Physician satisfaction | 71% | 4.8/5 | 63% | Target 85%+ |

---

## Sources Consulted

- [Accuro Keyboard Shortcuts (official PDF)](https://accuroemr.com/wp-content/uploads/2019/12/Accuro-Keyboard-Shortcuts-PC.pdf)
- [Accuro AI Scribe](https://accuroemr.com/clinic-tools/accuro-ai-scribe/)
- [Oscar vs Accuro — Capterra Canada](https://www.capterra.ca/compare/132058/166227/oscar/vs/accuro-emr)
- [Cortico — How to Choose an EMR in Canada](https://cortico.health/article/how-to-choose-an-emr/)
- [Physicians First — Ontario EMR Comparison](https://www.physiciansfirst.ca/resources/what-your-ontario-emr-choice-says-about-you-insights-for-ontario-physicians)
- [Tali AI — Guide to Canadian Primary Care EMR](https://tali.ai/resources/a-guide-to-canadian-primary-care-s-electronic-medical-record)
