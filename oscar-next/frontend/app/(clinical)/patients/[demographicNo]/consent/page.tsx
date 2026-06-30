"use client";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useParams } from "next/navigation";
import { fetchPatientConsent } from "@/lib/api/patients";
import { getCachedConsent, setCachedConsent } from "@/lib/patientCache";
import type { ConsentRecord } from "@/lib/types/patient";
import { formatDate } from "@/lib/utils";
import { Loader2, ShieldCheck, ShieldOff, Shield } from "lucide-react";
import { getAccessToken } from "@/lib/auth";

const CONSENT_TYPE_LABELS: Record<number, string> = {
  1: "Electronic Medical Record Sharing",
  2: "Patient Messaging & Email",
  3: "Research Use",
  4: "Teaching Use",
  5: "Third-Party Disclosure",
};

function ConsentBadge({ explicit, optout }: { explicit?: number | null; optout?: number | null }) {
  if (optout === 1) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-red-100 text-red-700">
        <ShieldOff className="w-3 h-3" /> Opted Out
      </span>
    );
  }
  if (explicit === 1) {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-green-100 text-green-700">
        <ShieldCheck className="w-3 h-3" /> Consented
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold bg-gray-100 text-gray-600">
      <Shield className="w-3 h-3" /> Not set
    </span>
  );
}

export default function ConsentPage() {
  const { data: session, status } = useSession();
  const params = useParams();
  const no = parseInt(params.demographicNo as string, 10);

  const [records, setRecords] = useState<ConsentRecord[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status !== "authenticated") return;
    const token = getAccessToken(session);

    const cached = getCachedConsent(no);
    if (cached) { setRecords(cached); setLoading(false); return; }

    fetchPatientConsent(token, no)
      .then(data => { setCachedConsent(no, data); setRecords(data); })
      .catch(() => setError("Failed to load consent records"))
      .finally(() => setLoading(false));
  }, [session, status, no]);

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error) {
    return <p className="text-center text-red-600 py-12">{error}</p>;
  }

  return (
    <div className="max-w-2xl mx-auto">
      <h2 className="text-base font-semibold text-gray-800 mb-4">Consent Records</h2>

      {records.length === 0 && (
        <div className="flex flex-col items-center py-16 text-gray-400">
          <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center mb-3">
            <Shield className="w-6 h-6 text-gray-300" />
          </div>
          <p className="text-sm">No consent records on file</p>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {records.map(record => {
          const typeLabel = record.consent_type_id
            ? (CONSENT_TYPE_LABELS[record.consent_type_id] ?? `Type ${record.consent_type_id}`)
            : "General Consent";

          return (
            <div key={record.id} className="p-4 bg-white rounded-xl border border-gray-200">
              <div className="flex items-start justify-between gap-3">
                <p className="text-sm font-medium text-gray-900">{typeLabel}</p>
                <ConsentBadge explicit={record.explicit} optout={record.optout} />
              </div>
              <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-500">
                {record.consent_date && (
                  <span>Consented: {formatDate(record.consent_date)}</span>
                )}
                {record.optout_date && (
                  <span>Opted out: {formatDate(record.optout_date)}</span>
                )}
                {record.edit_date && (
                  <span>Last edit: {formatDate(record.edit_date)}</span>
                )}
                {record.last_entered_by && (
                  <span>By: {record.last_entered_by}</span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
