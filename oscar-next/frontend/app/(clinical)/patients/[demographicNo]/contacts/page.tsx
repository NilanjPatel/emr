"use client";
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import { useParams } from "next/navigation";
import { fetchPatientContacts } from "@/lib/api/patients";
import { getAccessToken } from "@/lib/auth";
import { getCachedContacts, setCachedContacts } from "@/lib/patientCache";
import ContactCard from "@/components/clinical/PatientContacts/ContactCard";
import type { PatientContact } from "@/lib/types/patient";
import { Loader2, Users } from "lucide-react";

export default function ContactsPage() {
  const { data: session, status } = useSession();
  const params = useParams();
  const no = parseInt(params.demographicNo as string, 10);

  const [contacts, setContacts] = useState<PatientContact[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (status !== "authenticated") return;
    const token = getAccessToken(session);

    const cached = getCachedContacts(no);
    if (cached) { setContacts(cached); setLoading(false); return; }

    fetchPatientContacts(token, no)
      .then(data => { setCachedContacts(no, data); setContacts(data); })
      .catch(() => setError("Failed to load contacts"))
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

  const active = contacts.filter(c => c.active !== 0);
  const inactive = contacts.filter(c => c.active === 0);

  return (
    <div className="max-w-2xl mx-auto">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-base font-semibold text-gray-800">
          Contacts & SDM
          {active.length > 0 && (
            <span className="ml-2 text-xs font-normal text-gray-400">{active.length} active</span>
          )}
        </h2>
      </div>

      {active.length === 0 && (
        <div className="flex flex-col items-center py-16 text-gray-400">
          <div className="w-12 h-12 rounded-xl bg-gray-100 flex items-center justify-center mb-3">
            <Users className="w-6 h-6 text-gray-300" />
          </div>
          <p className="text-sm">No contacts on file</p>
        </div>
      )}

      <div className="flex flex-col gap-3">
        {active.map(link => (
          <ContactCard key={link.id} link={link} />
        ))}
      </div>

      {inactive.length > 0 && (
        <details className="mt-6">
          <summary className="text-xs text-gray-400 cursor-pointer hover:text-gray-600 select-none">
            {inactive.length} inactive contact{inactive.length === 1 ? "" : "s"}
          </summary>
          <div className="flex flex-col gap-3 mt-3">
            {inactive.map(link => (
              <ContactCard key={link.id} link={link} />
            ))}
          </div>
        </details>
      )}
    </div>
  );
}
