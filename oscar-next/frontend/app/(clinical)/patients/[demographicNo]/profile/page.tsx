"use client";
/**
 * Patient profile edit page — full demographic form with save.
 * Client component so we can handle react-hook-form state and session token.
 */
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useParams, useRouter } from "next/navigation";
import { fetchPatientDetail, updatePatient } from "@/lib/api/patients";
import { getAccessToken } from "@/lib/auth";
import DemographicForm from "@/components/clinical/PatientProfile/DemographicForm";
import { getCachedPatient, setCachedPatient, invalidatePatient } from "@/lib/patientCache";
import type { PatientDetail, PatientUpdate } from "@/lib/types/patient";
import { Loader2 } from "lucide-react";

export default function ProfilePage() {
  const { data: session, status } = useSession();
  const params = useParams();
  const router = useRouter();
  const no = parseInt(params.demographicNo as string, 10);

  const [patient, setPatient] = useState<PatientDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status !== "authenticated") return;
    let token: string;
    try { token = getAccessToken(session); } catch { setError("Session error"); return; }

    // Serve from cache if fresh — avoids redundant fetch when switching back from Summary
    const cached = getCachedPatient(no);
    if (cached) { setPatient(cached); setLoading(false); return; }

    fetchPatientDetail(token, no)
      .then(data => { setCachedPatient(no, data); setPatient(data); })
      .catch(() => setError("Failed to load patient"))
      .finally(() => setLoading(false));
  }, [session, status, no]);

  const handleSave = async (values: PatientUpdate) => {
    const token = getAccessToken(session);
    await updatePatient(token, no, values);
    // Invalidate so Summary shows fresh data on next visit
    invalidatePatient(no);
    router.refresh();
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-24">
        <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
      </div>
    );
  }

  if (error || !patient) {
    return <p className="text-center text-red-600 py-12">{error ?? "Patient not found"}</p>;
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* key forces remount when patient data loads so defaultValues are fresh */}
      <DemographicForm key={patient.demographic_no} patient={patient} onSave={handleSave} />
    </div>
  );
}
