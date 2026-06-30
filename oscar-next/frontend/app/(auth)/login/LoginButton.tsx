"use client";
import { useState, useTransition } from "react";
import { signIn } from "next-auth/react";
import { useSearchParams } from "next/navigation";
import { Eye, EyeOff, Loader2, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

export default function LoginForm() {
  const searchParams = useSearchParams();
  const callbackUrl = searchParams.get("callbackUrl") ?? "/schedule";
  const urlError    = searchParams.get("error");

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [totp, setTotp]         = useState("");
  const [showTotp, setShowTotp] = useState(false);
  const [showPw, setShowPw]     = useState(false);
  const [error, setError]       = useState<string | null>(
    urlError === "CredentialsSignin" ? "Invalid username or password." : null
  );
  const [pending, startTransition] = useTransition();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    startTransition(async () => {
      const res = await signIn("credentials", {
        username,
        password,
        totp: totp.trim() || undefined,
        callbackUrl,
        redirect: false,
      });
      if (res?.error) {
        // Keycloak returns specific error descriptions via ROPC
        if (res.error.includes("otp") || res.error.includes("totp") || res.error.includes("OTP")) {
          setShowTotp(true);
          setError("Your account has two-factor authentication enabled. Enter your authenticator code below.");
        } else {
          setError("Invalid username or password.");
        }
      } else if (res?.url) {
        window.location.href = res.url;
      }
    });
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Error banner */}
      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 px-3 py-2.5 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Username */}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="username" className="text-sm font-medium text-gray-700">
          Username
        </label>
        <input
          id="username"
          type="text"
          autoComplete="username"
          autoFocus
          required
          value={username}
          onChange={e => setUsername(e.target.value)}
          className={cn(
            "h-10 px-3 text-sm rounded-lg border bg-white outline-none transition-colors",
            "focus:border-blue-400 focus:ring-2 focus:ring-blue-100",
            "border-gray-300 hover:border-gray-400"
          )}
          placeholder="your.username"
        />
      </div>

      {/* Password */}
      <div className="flex flex-col gap-1.5">
        <label htmlFor="password" className="text-sm font-medium text-gray-700">
          Password
        </label>
        <div className="relative">
          <input
            id="password"
            type={showPw ? "text" : "password"}
            autoComplete="current-password"
            required
            value={password}
            onChange={e => setPassword(e.target.value)}
            className={cn(
              "w-full h-10 pl-3 pr-10 text-sm rounded-lg border bg-white outline-none transition-colors",
              "focus:border-blue-400 focus:ring-2 focus:ring-blue-100",
              "border-gray-300 hover:border-gray-400"
            )}
            placeholder="••••••••"
          />
          <button
            type="button"
            onClick={() => setShowPw(v => !v)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
            tabIndex={-1}
          >
            {showPw ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
          </button>
        </div>
      </div>

      {/* TOTP — shown if user has 2FA configured or after first failed attempt detected it */}
      {showTotp ? (
        <div className="flex flex-col gap-1.5">
          <label htmlFor="totp" className="text-sm font-medium text-gray-700 flex items-center gap-1.5">
            <ShieldCheck className="w-4 h-4 text-blue-600" />
            Authenticator code
          </label>
          <input
            id="totp"
            type="text"
            inputMode="numeric"
            autoComplete="one-time-code"
            autoFocus
            maxLength={8}
            value={totp}
            onChange={e => setTotp(e.target.value.replace(/\D/g, ""))}
            className={cn(
              "h-10 px-3 text-sm rounded-lg border bg-white outline-none transition-colors tracking-widest font-mono",
              "focus:border-blue-400 focus:ring-2 focus:ring-blue-100",
              "border-gray-300 hover:border-gray-400"
            )}
            placeholder="000000"
          />
          <p className="text-xs text-gray-500">
            Enter the 6-digit code from your authenticator app (e.g. Google Authenticator, Authy).
          </p>
        </div>
      ) : (
        <button
          type="button"
          onClick={() => setShowTotp(true)}
          className="text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
        >
          <ShieldCheck className="w-3 h-3" />
          I have a two-factor authenticator code
        </button>
      )}

      {/* Submit */}
      <button
        type="submit"
        disabled={pending || !username || !password}
        className={cn(
          "w-full flex items-center justify-center gap-2 h-10 rounded-xl text-white text-sm font-medium transition-colors",
          "bg-blue-600 hover:bg-blue-700 active:bg-blue-800",
          "focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2",
          "disabled:opacity-60 disabled:cursor-not-allowed"
        )}
      >
        {pending && <Loader2 className="w-4 h-4 animate-spin" />}
        {pending ? "Signing in…" : "Sign in"}
      </button>
    </form>
  );
}
