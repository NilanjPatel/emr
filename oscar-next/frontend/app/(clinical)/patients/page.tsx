/**
 * /patients — Patient search page (Server Component shell, client search widget).
 * Initial render: empty state or recently accessed list.
 * Interactive search runs client-side via PatientSearch component.
 */
import { requireSession } from "@/lib/auth";
import { Users, UserPlus } from "lucide-react";
import Link from "next/link";
import PatientSearch from "@/components/clinical/PatientSearch/PatientSearch";

export const metadata = { title: "Patients — Oscar EMR" };

export default async function PatientsPage() {
  await requireSession();

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Patients</h1>
          <p className="text-sm text-gray-500 mt-0.5">Search by name, HIN, chart number, or phone</p>
        </div>
        <Link
          href="/patients/new"
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 transition-colors"
        >
          <UserPlus className="w-4 h-4" />
          New Patient
        </Link>
      </div>

      {/* Search widget — client component, handles its own state */}
      <PatientSearch autoFocus inline />

      {/* Empty state */}
      <div className="mt-16 flex flex-col items-center text-center text-gray-400">
        <div className="w-16 h-16 rounded-2xl bg-gray-100 flex items-center justify-center mb-4">
          <Users className="w-8 h-8 text-gray-300" />
        </div>
        <p className="text-sm font-medium text-gray-500">Start typing to search patients</p>
        <p className="text-xs mt-1">
          Tip: press <kbd className="font-mono bg-gray-100 px-1 py-0.5 rounded text-gray-500">⌘K</kbd> from anywhere to search
        </p>
      </div>
    </div>
  );
}
