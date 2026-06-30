"use client";
/**
 * Patient summary page — client component so DB hiccups show a recoverable
 * spinner rather than a hard SSR 500. Uses sessionStorage cache so switching
 * tabs and back doesn't re-fetch within the 5-minute TTL.
 */
import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { useSession } from "next-auth/react";
import { Loader2, ChevronRight } from "lucide-react";
import Link from "next/link";
import { fetchPatientDetail } from "@/lib/api/patients";
import { getCachedPatient, setCachedPatient } from "@/lib/patientCache";
import { formatDate } from "@/lib/utils";
import type { PatientDetail } from "@/lib/types/patient";
import type { OscarSession } from "@/lib/auth";

const SEX_LABELS: Record<string, string> = {
  M: "Male", F: "Female", O: "Other", U: "Unknown", T: "Transgender", I: "Intersex",
};

function InfoRow({ label, value }: { label: string; value?: string | null }) {
  if (!value) return null;
  return (
    <div className="flex items-start gap-3 py-2 border-b border-gray-50 last:border-0">
      <dt className="w-40 text-xs font-medium text-gray-500 flex-shrink-0 pt-0.5">{label}</dt>
      <dd className="text-sm text-gray-900">{value}</dd>
    </div>
  );
}

function SummaryCard({
  title,
  href,
  children,
}: {
  title: string;
  href: string;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <h2 className="text-sm font-semibold text-gray-700">{title}</h2>
        <Link href={href} className="flex items-center gap-1 text-xs text-blue-600 hover:underline">
          Edit <ChevronRight className="w-3 h-3" />
        </Link>
      </div>
      <dl className="px-4 py-2">{children}</dl>
    </div>
  );
}

export default function PatientSummaryPage() {
  const params  = useParams<{ demographicNo: string }>();
  const no      = parseInt(params.demographicNo, 10);
  const { data: session, status } = useSession();
  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error,   setError]   = useState<string | null>(null);

  useEffect(() => {
    if (status !== "authenticated" || isNaN(no)) return;

    // Serve from cache if fresh
    const cached = getCachedPatient(no);
    if (cached) { setPatient(cached); setLoading(false); return; }

    const token = (session as OscarSession)?.accessToken;
    if (!token) { setError("Session expired. Please refresh."); setLoading(false); return; }

    fetchPatientDetail(token, no)
      .then(data => {
        setCachedPatient(no, data);
        setPatient(data);
      })
      .catch(err => {
        const msg = String(err?.message ?? err);
        setError(msg.includes("404") ? "Patient not found." : "Failed to load patient data. Please refresh or try again.");
      })
      .finally(() => setLoading(false));
  }, [status, no, session]);

  if (loading || status === "loading") {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error || !patient) {
    return (
      <div className="max-w-3xl mx-auto p-6 text-center text-red-600 text-sm">
        {error ?? "Failed to load patient data. Please refresh or try again."}
      </div>
    );
  }

  const base   = `/patients/${no}`;
  const dob    = patient.dob_iso ? formatDate(patient.dob_iso) : undefined;
  const dobAge = dob && patient.age != null ? `${dob}  (${patient.age}y)` : dob;

  return (
    <div className="max-w-3xl mx-auto grid grid-cols-1 gap-4">
      {/* Identity */}
      <SummaryCard title="Personal" href={`${base}/profile#section-personal`}>
        <InfoRow label="Full Name"
          value={[patient.title, patient.first_name, patient.middle_names, patient.last_name]
            .filter(Boolean).join(" ")} />
        <InfoRow label="Preferred Name" value={patient.pref_name} />
        <InfoRow label="Alias" value={patient.alias} />
        <InfoRow label="Sex" value={SEX_LABELS[patient.sex] ?? patient.sex} />
        <InfoRow label="Date of Birth" value={dobAge} />
        <InfoRow label="Chart No." value={patient.chart_no} />
        <InfoRow label="Status" value={patient.patient_status_label ?? patient.patient_status} />
      </SummaryCard>

      {/* Contact */}
      <SummaryCard title="Contact" href={`${base}/profile#section-contact`}>
        <InfoRow label="Phone (Home)" value={patient.phone} />
        <InfoRow label="Phone (Mobile)" value={patient.phone2} />
        <InfoRow label="Email" value={patient.email} />
        <InfoRow label="Mailing Address"
          value={[patient.address, patient.city, patient.province, patient.postal]
            .filter(Boolean).join(", ") || undefined} />
      </SummaryCard>

      {/* Health Card */}
      <SummaryCard title="Health Card" href={`${base}/profile#section-health`}>
        <InfoRow label="HIN" value={patient.hin ? `${patient.hin} ${patient.ver ?? ""}`.trim() : undefined} />
        <InfoRow label="Province" value={patient.hc_type} />
        <InfoRow label="Renewal Date" value={patient.hc_renew_date ? formatDate(patient.hc_renew_date) : undefined} />
      </SummaryCard>

      {/* Provider */}
      <SummaryCard title="Provider & Enrolment" href={`${base}/profile#section-provider`}>
        <InfoRow label="Provider No." value={patient.provider_no} />
        <InfoRow label="Roster Status" value={patient.roster_status} />
        <InfoRow label="Roster Date" value={patient.roster_date ? formatDate(patient.roster_date) : undefined} />
        <InfoRow label="Official Language" value={patient.official_lang} />
      </SummaryCard>

      {/* Audit */}
      <div className="text-xs text-gray-400 text-right">
        Last updated by {patient.lastUpdateUser ?? "—"} on {patient.lastUpdateDate ? formatDate(patient.lastUpdateDate) : "—"}
      </div>
    </div>
  );
}
