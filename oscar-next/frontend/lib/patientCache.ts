/**
 * sessionStorage cache for patient data.
 * Keyed by demographicNo — tab-scoped, never persists across sessions.
 * TTL prevents serving stale data after edits or prolonged idle time.
 */
import type { PatientDetail, PatientContact, ConsentRecord } from "@/lib/types/patient";

const DETAIL_TTL  = 5 * 60 * 1000;  // 5 minutes
const CONTACT_TTL = 2 * 60 * 1000;  // 2 minutes
const CONSENT_TTL = 5 * 60 * 1000;  // 5 minutes

interface Envelope<T> {
  data: T;
  ts: number;
}

function read<T>(key: string, ttl: number): T | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(key);
    if (!raw) return null;
    const { data, ts } = JSON.parse(raw) as Envelope<T>;
    if (Date.now() - ts > ttl) { sessionStorage.removeItem(key); return null; }
    return data;
  } catch {
    return null;
  }
}

function write<T>(key: string, data: T) {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(key, JSON.stringify({ data, ts: Date.now() } satisfies Envelope<T>));
  } catch {
    // sessionStorage full or disabled — silently skip caching
  }
}

function remove(key: string) {
  if (typeof window === "undefined") return;
  try { sessionStorage.removeItem(key); } catch { /* ignore */ }
}

// ── Patient detail ───────────────────────────────────────────────────────────

export function getCachedPatient(no: number): PatientDetail | null {
  return read<PatientDetail>(`patient_detail_${no}`, DETAIL_TTL);
}

export function setCachedPatient(no: number, data: PatientDetail) {
  write(`patient_detail_${no}`, data);
}

export function invalidatePatient(no: number) {
  remove(`patient_detail_${no}`);
}

// ── Contacts ─────────────────────────────────────────────────────────────────

export function getCachedContacts(no: number): PatientContact[] | null {
  return read<PatientContact[]>(`patient_contacts_${no}`, CONTACT_TTL);
}

export function setCachedContacts(no: number, data: PatientContact[]) {
  write(`patient_contacts_${no}`, data);
}

export function invalidateContacts(no: number) {
  remove(`patient_contacts_${no}`);
}

// ── Consent ──────────────────────────────────────────────────────────────────

export function getCachedConsent(no: number): ConsentRecord[] | null {
  return read<ConsentRecord[]>(`patient_consent_${no}`, CONSENT_TTL);
}

export function setCachedConsent(no: number, data: ConsentRecord[]) {
  write(`patient_consent_${no}`, data);
}

export function invalidateConsent(no: number) {
  remove(`patient_consent_${no}`);
}
