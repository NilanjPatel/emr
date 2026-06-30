import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/authOptions";

const FHIR_BASE = process.env.NEXT_PUBLIC_FHIR_BASE_URL ?? "http://localhost:8000/fhir/R4";

async function getAccessToken(): Promise<string | null> {
  const session = await getServerSession(authOptions);
  return (session as { accessToken?: string })?.accessToken ?? null;
}

export async function fhirGet<T>(path: string): Promise<T> {
  const token = await getAccessToken();
  const res = await fetch(`${FHIR_BASE}${path}`, {
    headers: {
      Authorization: token ? `Bearer ${token}` : "",
      Accept: "application/fhir+json",
    },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`FHIR ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}

export async function fhirPost<T>(path: string, body: unknown): Promise<T> {
  const token = await getAccessToken();
  const res = await fetch(`${FHIR_BASE}${path}`, {
    method: "POST",
    headers: {
      Authorization: token ? `Bearer ${token}` : "",
      "Content-Type": "application/fhir+json",
      Accept: "application/fhir+json",
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`FHIR POST ${path} → ${res.status}`);
  return res.json() as Promise<T>;
}
