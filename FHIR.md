# FHIR R4 Resource Mapping

## Oscar Data Model → FHIR R4

This file is the canonical mapping reference. Before designing any endpoint, check here first. If a mapping is missing, propose it here before implementing.

---

## Patient (demographic table)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `demographic_no` | `Patient.id` | Use as FHIR resource ID |
| `first_name` | `Patient.name[0].given[0]` | |
| `last_name` | `Patient.name[0].family` | |
| `date_of_birth` | `Patient.birthDate` | Format: YYYY-MM-DD |
| `sex` | `Patient.gender` | Oscar: M/F/O/U → FHIR: male/female/other/unknown |
| `hin` (health insurance number) | `Patient.identifier[type=PHN]` | Provincial health card number |
| `ver` (HIN version) | `Patient.identifier[type=PHN].period` | Ontario HIN version code |
| `address` | `Patient.address[0].line[0]` | |
| `city` | `Patient.address[0].city` | |
| `province` | `Patient.address[0].state` | |
| `postal` | `Patient.address[0].postalCode` | |
| `phone` | `Patient.telecom[system=phone, use=home]` | |
| `phone2` | `Patient.telecom[system=phone, use=work]` | |
| `email` | `Patient.telecom[system=email]` | |
| `patient_status` | `Patient.active` | AC=true, IN/DE=false |
| `date_joined` | `Patient.meta.lastUpdated` | |
| `provider_no` | `Patient.generalPractitioner` | Reference to Practitioner |
| `rostered_provider_no` | `Patient.generalPractitioner[1]` | |
| `chart_no` | `Patient.identifier[type=MR]` | Medical record number |

**Zero-date handling:** Oscar stores `0000-00-00` for unknown DOB. Map to `Patient.birthDate` absent (omit field).

---

## Provider (provider table)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `provider_no` | `Practitioner.id` | |
| `first_name` | `Practitioner.name[0].given[0]` | |
| `last_name` | `Practitioner.name[0].family` | |
| `ohip_no` | `Practitioner.identifier[type=OHIP]` | Ontario billing number |
| `specialty` | `Practitioner.qualification[0].code` | |
| `provider_type` | `Practitioner.qualification[0].code.coding` | MD, NP, RN, etc. |
| `email` | `Practitioner.telecom[system=email]` | |
| `work_phone` | `Practitioner.telecom[system=phone, use=work]` | |
| `status` | `Practitioner.active` | 1=true, 0=false |

---

## Appointment (appointment table)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `appointment_no` | `Appointment.id` | |
| `demographic_no` | `Appointment.participant[actor=Patient]` | |
| `provider_no` | `Appointment.participant[actor=Practitioner]` | |
| `appointment_date` + `start_time` | `Appointment.start` | Combine into ISO 8601 datetime |
| `appointment_date` + `end_time` | `Appointment.end` | |
| `status` | `Appointment.status` | See status mapping below |
| `reason` | `Appointment.reasonCode[0].text` | |
| `notes` | `Appointment.comment` | |
| `type` | `Appointment.serviceType[0].text` | |
| `location` | `Appointment.participant[actor=Location]` | |
| `urgency` | `Appointment.priority` | |
| `creator` | `Appointment.meta.source` | |

**Appointment Status Mapping:**
| Oscar `status` | FHIR `Appointment.status` |
|---|---|
| `A` (active/booked) | `booked` |
| `H` (home visit) | `booked` |
| `N` (no show) | `noshow` |
| `C` (cancelled) | `cancelled` |
| `B` (billed) | `fulfilled` |
| `T` (tentative) | `pending` |
| `E` (e-visit) | `booked` |
| `" "` (empty) | `proposed` |

---

## Schedule (rschedule + scheduledate tables)

| Concept | FHIR Resource | Notes |
|---|---|---|
| Provider availability template | `Schedule` | One per provider per date range |
| Individual available slot | `Slot` | Generated from schedule template |

---

## Encounter Note (casemgmt_note table)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `note_id` | `Composition.id` | |
| `demographic_no` | `Composition.subject` | Reference to Patient |
| `provider_no` | `Composition.author` | Reference to Practitioner |
| `observation_date` | `Composition.date` | |
| `note` | `Composition.section[0].text.div` | XHTML narrative |
| `signed` | `Composition.status` | signed=`final`, unsigned=`preliminary` |
| `type` | `Composition.type.coding` | LOINC code for note type |

**Encounter wrapper:** Each encounter session gets an `Encounter` resource. Composition is linked to Encounter via `Composition.encounter`.

---

## Condition / Problem (casemgmt_issue + Dxresearch)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `issue_id` | `Condition.id` | |
| `demographic_no` | `Condition.subject` | |
| `description` | `Condition.code.text` | |
| `icd9` | `Condition.code.coding[system=ICD-9]` | |
| `start_date` | `Condition.onsetDateTime` | |
| `end_date` | `Condition.abatementDateTime` | |
| `status` | `Condition.clinicalStatus` | active/resolved/inactive |

---

## AllergyIntolerance (allergies table)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `id` | `AllergyIntolerance.id` | |
| `demographic_no` | `AllergyIntolerance.patient` | |
| `description` | `AllergyIntolerance.code.text` | |
| `allergicReaction` | `AllergyIntolerance.reaction[0].manifestation[0].text` | |
| `severity` | `AllergyIntolerance.reaction[0].severity` | mild/moderate/severe |
| `startDate` | `AllergyIntolerance.onsetDateTime` | |
| `archived` | `AllergyIntolerance.clinicalStatus` | archived=inactive |
| `type` | `AllergyIntolerance.type` | allergy/intolerance |

---

## MedicationRequest / Prescription (prescription + prescribe tables)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `prescriptionId` | `MedicationRequest.id` | |
| `demographicId` | `MedicationRequest.subject` | |
| `providerNo` | `MedicationRequest.requester` | |
| `drugName` | `MedicationRequest.medicationCodeableConcept.text` | |
| `din` | `MedicationRequest.medicationCodeableConcept.coding[system=DIN]` | Drug Identification Number |
| `dosage` | `MedicationRequest.dosageInstruction[0].text` | |
| `quantity` | `MedicationRequest.dispenseRequest.quantity` | |
| `repeat` | `MedicationRequest.dispenseRequest.numberOfRepeatsAllowed` | |
| `writtenDate` | `MedicationRequest.authoredOn` | |
| `dateStarted` | `MedicationRequest.dispenseRequest.validityPeriod.start` | |
| `dateEnded` | `MedicationRequest.dispenseRequest.validityPeriod.end` | |
| `status` | `MedicationRequest.status` | active/stopped/completed |

---

## Observation / Measurement (measurements table)

| Concept | FHIR Resource | LOINC Code |
|---|---|---|
| Blood pressure (systolic) | `Observation` | 8480-6 |
| Blood pressure (diastolic) | `Observation` | 8462-4 |
| Height | `Observation` | 8302-2 |
| Weight | `Observation` | 29463-7 |
| BMI | `Observation` | 39156-5 |
| Heart rate | `Observation` | 8867-4 |
| Temperature | `Observation` | 8310-5 |
| Blood glucose | `Observation` | 2339-0 |
| A1C | `Observation` | 4548-4 |

---

## DiagnosticReport / Lab Results (labTestResults table)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `labPatientId` | `DiagnosticReport.subject` | → Patient |
| `reportDate` | `DiagnosticReport.effectiveDateTime` | |
| `labName` | `DiagnosticReport.performer` | → Organization |
| `testName` | `DiagnosticReport.code.text` | |
| individual results | `DiagnosticReport.result[]` | → array of `Observation` |
| `abnormal` | `Observation.interpretation` | H/L/N → high/low/normal |

---

## Immunization / Prevention (preventions table)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `id` | `Immunization.id` | |
| `demographic_no` | `Immunization.patient` | |
| `prevention_type` | `Immunization.vaccineCode` | Map to CVX codes |
| `prevention_date` | `Immunization.occurrenceDateTime` | |
| `provider_no` | `Immunization.performer[0].actor` | |
| `refused` | `Immunization.status` | refused=`not-done` |
| `next_date` | `ImmunizationRecommendation.recommendation[0].dateCriterion` | |

---

## Claim / Billing (billing + billingdetail tables)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `billing_no` | `Claim.id` | |
| `demographic_no` | `Claim.patient` | |
| `provider_no` | `Claim.provider` | |
| `billing_date` | `Claim.created` | |
| `dx_code` | `Claim.diagnosis[0].diagnosisCodeableConcept` | ICD-9/10 |
| `service_code` | `Claim.item[0].productOrService` | OHIP service code |
| `billed_amount` | `Claim.item[0].net` | |
| `paid_amount` | `ClaimResponse.item[0].adjudication[0].amount` | |
| `status` | `Claim.status` | active/cancelled/draft |

---

## DocumentReference (document table)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `document_no` | `DocumentReference.id` | |
| `demographic_no` | `DocumentReference.subject` | |
| `doc_type` | `DocumentReference.type.coding` | |
| `doc_desc` | `DocumentReference.description` | |
| `content_type` | `DocumentReference.content[0].attachment.contentType` | |
| `created_date` | `DocumentReference.date` | |
| file location | `DocumentReference.content[0].attachment.url` | signed URL to OscarDocument filesystem |

---

## Task / Tickler (tickler table)

| Oscar Field | FHIR Field | Notes |
|---|---|---|
| `tickler_no` | `Task.id` | |
| `demographic_no` | `Task.for` | → Patient |
| `provider_no` | `Task.owner` | → Practitioner |
| `message` | `Task.description` | |
| `service_date` | `Task.executionPeriod.start` | |
| `status` | `Task.status` | A=requested, C=completed |
| `priority` | `Task.priority` | |

---

## Practitioner Organization Context

| Oscar Concept | FHIR Resource |
|---|---|
| Clinic / facility | `Organization` |
| Site | `Location` |
| Department | `OrganizationAffiliation` |

---

## FHIR Base URL Convention

```
https://<clinic-domain>/fhir/R4/

Examples:
GET  /fhir/R4/Patient/12345
GET  /fhir/R4/Patient?name=Smith&birthdate=1970-01-15
POST /fhir/R4/Appointment
GET  /fhir/R4/Appointment?patient=12345&date=2026-07-01
POST /fhir/R4/$everything  (patient everything operation)
```

---

## SMART on FHIR Scopes

| Scope | Access |
|---|---|
| `patient/Patient.read` | Read patient demographics |
| `patient/Patient.write` | Edit patient demographics |
| `patient/Appointment.read` | Read appointments |
| `patient/Appointment.write` | Book/cancel appointments |
| `patient/MedicationRequest.read` | Read prescriptions |
| `patient/MedicationRequest.write` | Write prescriptions (requires `doctor` role) |
| `patient/DiagnosticReport.read` | Read lab results |
| `patient/Claim.write` | Submit billing (requires `billing` role) |
| `system/*.read` | System-level read (admin only) |
