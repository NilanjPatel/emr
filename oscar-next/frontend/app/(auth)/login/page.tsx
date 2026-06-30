import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/authOptions";
import { Suspense } from "react";
import LoginForm from "./LoginButton";

export const metadata = { title: "Sign in — Oscar EMR" };

export default async function LoginPage() {
  const session = await getServerSession(authOptions);
  if (session) redirect("/schedule");

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <div className="w-full max-w-sm space-y-8">
        {/* Logo + title */}
        <div className="text-center">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl bg-blue-600 text-white mb-4">
            <svg className="w-9 h-9" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h1 className="text-2xl font-semibold text-gray-900">Oscar EMR</h1>
          <p className="mt-1 text-sm text-gray-500">Maple Clinics — Secure sign in</p>
        </div>

        {/* Login card */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 space-y-5">
          <Suspense>
            <LoginForm />
          </Suspense>
          <p className="text-xs text-center text-gray-400">
            Secured by Keycloak · PHIPA compliant
          </p>
        </div>
      </div>
    </div>
  );
}
