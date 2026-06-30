"use client";
/**
 * Client-safe patient API wrapper.
 *
 * Uses axios with access token from NextAuth session — NOT fhirGet/fhirPost
 * which call getServerSession() and can only be used in server components.
 */
import axios, { type InternalAxiosRequestConfig } from "axios";
import { useSession } from "next-auth/react";
import { useMemo } from "react";
import type { OscarSession } from "@/lib/auth";
import type {
  PatientSearchResponse,
  PatientBanner,
  PatientDetail,
  PatientCreate,
  PatientUpdate,
  DuplicateCheckResponse,
  ExtField,
  PatientContact,
  ConsentRecord,
  MergeHistory,
} from "@/lib/types/patient";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

/**
 * Hook: returns an axios client pre-configured with the current session's access token.
 * Must be used inside a Client Component that is wrapped in SessionProvider.
 */
export function useApiClient() {
  const { data: session } = useSession();

  return useMemo(() => {
    const client = axios.create({ baseURL: API_BASE });
    client.interceptors.request.use((config: InternalAxiosRequestConfig) => {
      const token = (session as OscarSession)?.accessToken;
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });
    return client;
  }, [session]);
}

/**
 * Server-action-compatible fetch helpers (for use in Server Components / Route Handlers).
 * These accept an explicit access token rather than reading from session.
 */
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
  const url = new URL(`${API_BASE}/api/v1/patients/search`);
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== "") url.searchParams.set(k, String(v));
  });
  const res = await fetch(url.toString(), {
    headers: { Authorization: `Bearer ${token}`, Accept: "application/json" },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Patient search failed: ${res.status}`);
  return res.json();
}

export async function fetchPatientBanner(
  token: string,
  demographicNo: number
): Promise<PatientBanner> {
  const res = await fetch(`${API_BASE}/api/v1/patients/${demographicNo}/banner`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Banner fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchPatientDetail(
  token: string,
  demographicNo: number
): Promise<PatientDetail> {
  const res = await fetch(`${API_BASE}/api/v1/patients/${demographicNo}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Patient fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchPatientContacts(
  token: string,
  demographicNo: number
): Promise<PatientContact[]> {
  const res = await fetch(`${API_BASE}/api/v1/patients/${demographicNo}/contacts`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Contacts fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchPatientConsent(
  token: string,
  demographicNo: number
): Promise<ConsentRecord[]> {
  const res = await fetch(`${API_BASE}/api/v1/patients/${demographicNo}/consent`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Consent fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchPatientExt(
  token: string,
  demographicNo: number
): Promise<ExtField[]> {
  const res = await fetch(`${API_BASE}/api/v1/patients/${demographicNo}/ext`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Ext fields fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchMergeHistory(
  token: string,
  demographicNo: number
): Promise<MergeHistory[]> {
  const res = await fetch(`${API_BASE}/api/v1/patients/${demographicNo}/merge-history`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Merge history fetch failed: ${res.status}`);
  return res.json();
}

export async function fetchDuplicates(
  token: string,
  demographicNo: number
): Promise<DuplicateCheckResponse> {
  const res = await fetch(`${API_BASE}/api/v1/patients/${demographicNo}/duplicates`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`Duplicate check failed: ${res.status}`);
  return res.json();
}

export async function createPatient(
  token: string,
  data: PatientCreate
): Promise<PatientDetail> {
  const res = await fetch(`${API_BASE}/api/v1/patients`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.message ?? `Create patient failed: ${res.status}`);
  }
  return res.json();
}

export async function updatePatient(
  token: string,
  demographicNo: number,
  data: PatientUpdate
): Promise<PatientDetail> {
  const res = await fetch(`${API_BASE}/api/v1/patients/${demographicNo}`, {
    method: "PATCH",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.message ?? `Update patient failed: ${res.status}`);
  }
  return res.json();
}

export async function mergePatients(
  token: string,
  survivingNo: number,
  absorbedNo: number,
  reason?: string
): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE}/api/v1/patients/${survivingNo}/merge/${absorbedNo}`, {
    method: "POST",
    headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" },
    body: JSON.stringify({ reason: reason ?? "" }),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.message ?? `Merge failed: ${res.status}`);
  }
  return res.json();
}
