/**
 * Server-side patient API helpers — use these in Server Components and layouts.
 *
 * Uses API_INTERNAL_URL at runtime (Docker network, no Cloudflare hop) so server
 * components don't round-trip through the public tunnel and hit stale containers.
 * Falls back to NEXT_PUBLIC_API_BASE_URL if the internal URL is not set.
 *
 * Never import this file in a "use client" component.
 */
import type {
  PatientSearchResponse,
  PatientBanner,
  PatientDetail,
  PatientContact,
  ConsentRecord,
  ExtField,
  MergeHistory,
  DuplicateCheckResponse,
} from "@/lib/types/patient";

function apiBase(): string {
  // API_INTERNAL_URL is a server-only runtime env var (not NEXT_PUBLIC_)
  // Set to http://oscar-api:8000 in docker-compose for direct container-to-container fetch
  return (
    process.env.API_INTERNAL_URL ??
    process.env.NEXT_PUBLIC_API_BASE_URL ??
    "http://localhost:8000"
  );
}

function headers(token: string) {
  return { Authorization: `Bearer ${token}`, Accept: "application/json" };
}

export async function fetchPatientSearch(
  token: string,
  params: {
    q?: string;
    hin?: string;
    chart_no?: string;
    phone?: string;
    email?: string;
    include_inactive?: boolean;
    limit?: number;
    page?: number;
  }
): Promise<PatientSearchResponse> {
  const url = new URL(`${apiBase()}/api/v1/patients/search`);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") url.searchParams.set(k, String(v));
  });
  const res = await fetch(url.toString(), { headers: headers(token), cache: "no-store" });
  if (!res.ok) throw new Error(`Patient search failed: ${res.status}`);
  return res.json();
}

export async function fetchPatientBanner(
  token: string,
  demographicNo: number
): Promise<PatientBanner> {
  const res = await fetch(`${apiBase()}/api/v1/patients/${demographicNo}/banner`, {
    headers: headers(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Banner fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchPatientDetail(
  token: string,
  demographicNo: number
): Promise<PatientDetail> {
  const res = await fetch(`${apiBase()}/api/v1/patients/${demographicNo}`, {
    headers: headers(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Patient fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchPatientContacts(
  token: string,
  demographicNo: number
): Promise<PatientContact[]> {
  const res = await fetch(`${apiBase()}/api/v1/patients/${demographicNo}/contacts`, {
    headers: headers(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Contacts fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchPatientConsent(
  token: string,
  demographicNo: number
): Promise<ConsentRecord[]> {
  const res = await fetch(`${apiBase()}/api/v1/patients/${demographicNo}/consent`, {
    headers: headers(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Consent fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchPatientExt(
  token: string,
  demographicNo: number
): Promise<ExtField[]> {
  const res = await fetch(`${apiBase()}/api/v1/patients/${demographicNo}/ext`, {
    headers: headers(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Ext fields fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchMergeHistory(
  token: string,
  demographicNo: number
): Promise<MergeHistory[]> {
  const res = await fetch(`${apiBase()}/api/v1/patients/${demographicNo}/merge-history`, {
    headers: headers(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Merge history fetch failed: ${res.status}`);
  return res.json();
}

export async function createPatient(
  token: string,
  data: import("@/lib/types/patient").PatientCreate
): Promise<PatientDetail> {
  const res = await fetch(`${apiBase()}/api/v1/patients`, {
    method: "POST",
    headers: { ...headers(token), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { message?: string })?.message ?? `Create patient failed: ${res.status}`);
  }
  return res.json();
}

export async function updatePatient(
  token: string,
  demographicNo: number,
  data: import("@/lib/types/patient").PatientUpdate
): Promise<PatientDetail> {
  const res = await fetch(`${apiBase()}/api/v1/patients/${demographicNo}`, {
    method: "PATCH",
    headers: { ...headers(token), "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error((err as { message?: string })?.message ?? `Update patient failed: ${res.status}`);
  }
  return res.json();
}

export async function fetchDuplicates(
  token: string,
  demographicNo: number
): Promise<DuplicateCheckResponse> {
  const res = await fetch(`${apiBase()}/api/v1/patients/${demographicNo}/duplicates`, {
    headers: headers(token),
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Duplicate check failed: ${res.status}`);
  return res.json();
}
