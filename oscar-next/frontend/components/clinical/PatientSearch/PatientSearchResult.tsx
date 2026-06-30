"use client";
import { cn } from "@/lib/utils";
import { PATIENT_STATUS_COLORS, type PatientSearchResult } from "@/lib/types/patient";

interface Props {
  patient: PatientSearchResult;
  isSelected: boolean;
  onSelect: (p: PatientSearchResult) => void;
}

function initials(first: string, last: string): string {
  return `${first[0] ?? ""}${last[0] ?? ""}`.toUpperCase();
}

export default function PatientSearchResult({ patient, isSelected, onSelect }: Props) {
  const statusColor = PATIENT_STATUS_COLORS[patient.patient_status ?? ""] ?? "bg-gray-100 text-gray-700";

  return (
    <button
      onClick={() => onSelect(patient)}
      className={cn(
        "w-full flex items-center gap-3 px-4 py-2.5 text-left transition-colors",
        isSelected ? "bg-blue-50" : "hover:bg-gray-50"
      )}
    >
      {/* Avatar */}
      <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 flex items-center justify-center text-xs font-semibold flex-shrink-0">
        {initials(patient.first_name, patient.last_name)}
      </div>

      {/* Name + meta */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className={cn("text-sm font-medium", isSelected ? "text-blue-900" : "text-gray-900")}>
            {patient.last_name}, {patient.first_name}
            {patient.pref_name && patient.pref_name !== patient.first_name
              ? <span className="text-gray-400 font-normal"> ({patient.pref_name})</span>
              : null}
          </span>
          {patient.patient_status && (
            <span className={cn("text-[10px] font-semibold px-1.5 py-0.5 rounded-full", statusColor)}>
              {patient.patient_status}
            </span>
          )}
        </div>
        <p className="text-xs text-gray-500 truncate">
          {patient.dob_iso
            ? `DOB: ${patient.dob_iso}${patient.age != null ? ` · ${patient.age}y` : ""}`
            : "DOB unknown"}
          {patient.hin ? ` · HIN: ${patient.hin}` : ""}
          {patient.chart_no ? ` · Chart: ${patient.chart_no}` : ""}
        </p>
      </div>

      {patient.provider_no && (
        <span className="text-xs text-gray-400 flex-shrink-0">Dr {patient.provider_no}</span>
      )}
    </button>
  );
}
