"use client";
/**
 * New patient registration page.
 * Includes async duplicate detection: fires on blur of DOB + last name.
 * If score ≥ 75, shows warning panel. Score ≥ 90 requires explicit confirmation before save.
 */
import { useState, useCallback } from "react";
import { useForm, type SubmitHandler } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useSession } from "next-auth/react";
import { useRouter } from "next/navigation";
import { createPatient, fetchPatientSearch } from "@/lib/api/patients.server";
import { getAccessToken } from "@/lib/auth";
import type { PatientSearchResult } from "@/lib/types/patient";
import { AlertTriangle, Loader2, UserPlus } from "lucide-react";
import Link from "next/link";
import { cn } from "@/lib/utils";

const schema = z.object({
  first_name:     z.string().min(1, "Required"),
  last_name:      z.string().min(1, "Required"),
  sex:            z.enum(["M", "F", "O", "U", "T", "I"]),
  year_of_birth:  z.string().regex(/^\d{4}$/, "4-digit year").optional().or(z.literal("")),
  month_of_birth: z.string().regex(/^\d{1,2}$/, "1–2 digit month").optional().or(z.literal("")),
  date_of_birth:  z.string().regex(/^\d{1,2}$/, "1–2 digit day").optional().or(z.literal("")),
  phone:          z.string().optional(),
  email:          z.string().email("Invalid email").optional().or(z.literal("")),
  hin:            z.string().max(20).optional(),
  hc_type:        z.string().optional(),
  provider_no:    z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs font-medium text-gray-600">{label}</label>
      {children}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

function Input({ error, className, ...props }: React.InputHTMLAttributes<HTMLInputElement> & { error?: boolean }) {
  return (
    <input
      className={cn(
        "h-9 px-3 text-sm rounded-lg border bg-white outline-none transition-colors",
        "focus:border-blue-400 focus:ring-2 focus:ring-blue-100",
        error ? "border-red-400" : "border-gray-200 hover:border-gray-300",
        className
      )}
      {...props}
    />
  );
}

function Select({ error, children, ...props }: React.SelectHTMLAttributes<HTMLSelectElement> & { error?: boolean }) {
  return (
    <select
      className={cn(
        "h-9 px-3 text-sm rounded-lg border bg-white outline-none cursor-pointer",
        "focus:border-blue-400 focus:ring-2 focus:ring-blue-100",
        error ? "border-red-400" : "border-gray-200 hover:border-gray-300"
      )}
      {...props}
    >
      {children}
    </select>
  );
}

export default function NewPatientPage() {
  const { data: session } = useSession();
  const router = useRouter();
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [duplicates, setDuplicates] = useState<PatientSearchResult[]>([]);
  const [dupScore, setDupScore] = useState(0);
  const [confirmed, setConfirmed] = useState(false);

  const { register, handleSubmit, getValues, formState: { errors } } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { sex: "U" },
  });

  const checkDuplicates = useCallback(async () => {
    const { first_name, last_name, year_of_birth, month_of_birth, date_of_birth } = getValues();
    let token: string;
    try { token = getAccessToken(session); } catch { return; }
    if (!last_name || last_name.length < 2) return;

    const q = `${last_name} ${first_name}`.trim();
    try {
      const res = await fetchPatientSearch(token, { q, limit: 5 });
      if (res.results.length > 0) {
        // Score: DOB match + last_name match
        const scored = res.results.filter(p => {
          if (!p.dob_iso) return false;
          const [py, pm, pd] = p.dob_iso.split("-");
          return py === year_of_birth && pm === month_of_birth?.padStart(2, "0") && pd === date_of_birth?.padStart(2, "0");
        });
        if (scored.length > 0) {
          setDuplicates(scored);
          setDupScore(90);
        } else if (res.results.length > 0) {
          setDuplicates(res.results.slice(0, 3));
          setDupScore(60);
        }
      } else {
        setDuplicates([]);
        setDupScore(0);
      }
    } catch {
      // Non-fatal
    }
  }, [session, getValues]);

  const onSubmit: SubmitHandler<FormValues> = async (values) => {
    if (dupScore >= 90 && !confirmed) return;
    const token = getAccessToken(session);
    setSaving(true);
    setSaveError(null);
    try {
      const patient = await createPatient(token, values);
      router.push(`/patients/${patient.demographic_no}`);
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Failed to create patient");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-6">
        <div className="w-9 h-9 rounded-xl bg-blue-600 flex items-center justify-center">
          <UserPlus className="w-5 h-5 text-white" />
        </div>
        <div>
          <h1 className="text-lg font-bold text-gray-900">New Patient</h1>
          <p className="text-xs text-gray-500">Required fields are marked *</p>
        </div>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-6">

        {/* Identity */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Identity</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="First Name *" error={errors.first_name?.message}>
              <Input {...register("first_name")} error={!!errors.first_name} onBlur={checkDuplicates} />
            </Field>
            <Field label="Last Name *" error={errors.last_name?.message}>
              <Input {...register("last_name")} error={!!errors.last_name} onBlur={checkDuplicates} />
            </Field>
            <Field label="Sex *" error={errors.sex?.message}>
              <Select {...register("sex")} error={!!errors.sex}>
                <option value="M">Male</option>
                <option value="F">Female</option>
                <option value="O">Other</option>
                <option value="U">Unknown</option>
                <option value="T">Transgender</option>
                <option value="I">Intersex</option>
              </Select>
            </Field>
            <div className="flex flex-col gap-1">
              <label className="text-xs font-medium text-gray-600">Date of Birth</label>
              <div className="flex gap-2">
                <Input {...register("year_of_birth")}  placeholder="YYYY" className="w-20 text-center" onBlur={checkDuplicates} />
                <Input {...register("month_of_birth")} placeholder="MM"   className="w-16 text-center" onBlur={checkDuplicates} />
                <Input {...register("date_of_birth")}  placeholder="DD"   className="w-16 text-center" onBlur={checkDuplicates} />
              </div>
            </div>
          </div>
        </div>

        {/* Duplicate warning */}
        {duplicates.length > 0 && (
          <div className={cn(
            "rounded-xl border p-4",
            dupScore >= 90
              ? "bg-red-50 border-red-300"
              : "bg-amber-50 border-amber-300"
          )}>
            <div className="flex items-start gap-2">
              <AlertTriangle className={cn("w-4 h-4 mt-0.5 flex-shrink-0", dupScore >= 90 ? "text-red-600" : "text-amber-600")} />
              <div className="flex-1">
                <p className={cn("text-sm font-semibold", dupScore >= 90 ? "text-red-800" : "text-amber-800")}>
                  {dupScore >= 90 ? "Likely duplicate — strong match found" : "Possible duplicate patient"}
                </p>
                <ul className="mt-2 space-y-1">
                  {duplicates.map(p => (
                    <li key={p.demographic_no} className="text-xs text-gray-700 flex items-center gap-2">
                      <span>{p.last_name}, {p.first_name} — {p.dob_iso ?? "DOB unknown"}</span>
                      <Link href={`/patients/${p.demographic_no}`} target="_blank"
                        className="text-blue-600 hover:underline">View</Link>
                    </li>
                  ))}
                </ul>
                {dupScore >= 90 && (
                  <label className="mt-3 flex items-center gap-2 text-sm text-red-800 cursor-pointer">
                    <input type="checkbox" checked={confirmed} onChange={e => setConfirmed(e.target.checked)} />
                    I have reviewed the potential duplicates and confirm this is a new patient
                  </label>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Contact */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Contact</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="Phone">
              <Input {...register("phone")} type="tel" placeholder="416-555-0000" />
            </Field>
            <Field label="Email" error={errors.email?.message}>
              <Input {...register("email")} type="email" error={!!errors.email} />
            </Field>
          </div>
        </div>

        {/* Health Card */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Health Card</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Field label="HIN">
              <Input {...register("hin")} maxLength={20} />
            </Field>
            <Field label="Province">
              <Input {...register("hc_type")} placeholder="ON" maxLength={10} />
            </Field>
          </div>
        </div>

        {/* Provider */}
        <div className="bg-white rounded-xl border border-gray-200 p-5">
          <h2 className="text-sm font-semibold text-gray-700 mb-4">Provider</h2>
          <Field label="Provider No.">
            <Input {...register("provider_no")} className="w-40" />
          </Field>
        </div>

        {saveError && (
          <p className="text-sm text-red-600 text-center">{saveError}</p>
        )}

        <div className="flex gap-3 justify-end">
          <Link href="/patients"
            className="px-4 py-2 text-sm text-gray-600 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
            Cancel
          </Link>
          <button
            type="submit"
            disabled={saving || (dupScore >= 90 && !confirmed)}
            className="flex items-center gap-2 px-5 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors"
          >
            {saving && <Loader2 className="w-4 h-4 animate-spin" />}
            {saving ? "Creating…" : "Create Patient"}
          </button>
        </div>
      </form>
    </div>
  );
}
