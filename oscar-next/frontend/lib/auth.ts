import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import type { Session } from "next-auth";
import { authOptions } from "@/lib/authOptions";

/** next-auth Session extended with the Keycloak access_token we store in the JWT callback. */
export interface OscarSession extends Session {
  accessToken: string;
}

/** Extracts the access token from a session object (client or server). Throws if absent. */
export function getAccessToken(session: Session | null): string {
  const token = (session as OscarSession)?.accessToken;
  if (!token) throw new Error("No access token in session");
  return token;
}

export async function requireSession(): Promise<Session> {
  const session = await getServerSession(authOptions);
  if (!session) redirect("/login");
  return session;
}

export function hasRole(session: Session, role: string): boolean {
  return session?.user?.roles?.includes(role) ?? false;
}

export function isClinician(session: Session): boolean {
  return hasRole(session, "doctor") || hasRole(session, "nurse") || hasRole(session, "nurse_practitioner");
}
