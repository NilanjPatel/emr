/**
 * Shared NextAuth options — imported by both the route handler and server components.
 * Keep this file server-only (no "use client").
 */
import type { NextAuthOptions } from "next-auth";
import CredentialsProvider from "next-auth/providers/credentials";

const KEYCLOAK_ISSUER    = process.env.KEYCLOAK_ISSUER!;
const KEYCLOAK_CLIENT_ID = process.env.KEYCLOAK_CLIENT_ID!;
const KEYCLOAK_CLIENT_SECRET = process.env.KEYCLOAK_CLIENT_SECRET ?? "";
const TOKEN_ENDPOINT = `${KEYCLOAK_ISSUER}/protocol/openid-connect/token`;

interface KeycloakTokenResponse {
  access_token: string;
  id_token?: string;
  expires_in: number;
  error?: string;
  error_description?: string;
}

async function keycloakPasswordGrant(
  username: string,
  password: string,
  totp?: string
): Promise<KeycloakTokenResponse> {
  const body = new URLSearchParams({
    grant_type:    "password",
    client_id:     KEYCLOAK_CLIENT_ID,
    username,
    password,
    scope:         "openid email profile roles",
  });
  if (KEYCLOAK_CLIENT_SECRET) body.set("client_secret", KEYCLOAK_CLIENT_SECRET);
  if (totp) body.set("totp", totp);

  const res = await fetch(TOKEN_ENDPOINT, {
    method:  "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
    cache:   "no-store",
  });
  return res.json() as Promise<KeycloakTokenResponse>;
}

export const authOptions: NextAuthOptions = {
  providers: [
    CredentialsProvider({
      id:   "credentials",
      name: "Oscar EMR",
      credentials: {
        username: { label: "Username", type: "text" },
        password: { label: "Password", type: "password" },
        totp:     { label: "Authenticator code", type: "text" },
      },
      async authorize(credentials) {
        if (!credentials?.username || !credentials.password) return null;
        try {
          const data = await keycloakPasswordGrant(
            credentials.username,
            credentials.password,
            credentials.totp || undefined
          );
          if (data.error) throw new Error(data.error_description ?? data.error);

          const payload = JSON.parse(
            Buffer.from(data.access_token.split(".")[1], "base64url").toString()
          ) as {
            sub: string;
            preferred_username?: string;
            email?: string;
            name?: string;
            realm_access?: { roles?: string[] };
          };

          return {
            id:          payload.sub,
            name:        payload.name ?? payload.preferred_username ?? credentials.username,
            email:       payload.email ?? "",
            accessToken: data.access_token,
            idToken:     data.id_token,
            roles:       payload.realm_access?.roles ?? [],
            providerId:  payload.preferred_username ?? credentials.username,
          };
        } catch {
          return null;
        }
      },
    }),

  ],

  session: { strategy: "jwt", maxAge: 8 * 60 * 60 },

  callbacks: {
    async jwt({ token, user, account }) {
      if (user && "accessToken" in user) {
        const u = user as Record<string, unknown>;
        token.accessToken = u.accessToken as string;
        token.idToken     = u.idToken as string | undefined;
        token.roles       = u.roles as string[];
        token.providerId  = u.providerId as string;
      }
      if (account?.access_token) {
        token.accessToken = account.access_token;
        token.idToken     = account.id_token as string | undefined;
        token.expiresAt   = account.expires_at;
        try {
          const payload = JSON.parse(
            Buffer.from(account.access_token.split(".")[1], "base64url").toString()
          ) as { realm_access?: { roles?: string[] }; preferred_username?: string };
          token.roles      = payload.realm_access?.roles ?? [];
          token.providerId = payload.preferred_username ?? "";
        } catch {
          token.roles = [];
        }
      }
      return token;
    },

    async session({ session, token }) {
      const s = session as typeof session & { accessToken?: string };
      s.accessToken       = token.accessToken as string;
      session.user.roles  = (token.roles as string[]) ?? [];
      session.user.providerId = (token.providerId as string) ?? "";
      return session;
    },
  },

  pages: { signIn: "/login", error: "/login" },
};
