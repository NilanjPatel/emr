"use client";
import { cn } from "@/lib/utils";
import { PATIENT_STATUS_COLORS } from "@/lib/types/patient";

const STATUS_LABELS: Record<string, string> = {
  AC: "Active",
  IN: "Inactive",
  DE: "Deceased",
  MO: "Moved Out",
  NE: "Newborn",
  SP: "Suspended",
};

export default function PatientStatusChip({
  status,
  date,
}: {
  status: string | null | undefined;
  date?: string | null;
}) {
  if (!status) return null;
  const colorClass = PATIENT_STATUS_COLORS[status] ?? "bg-gray-100 text-gray-700";
  const label = STATUS_LABELS[status] ?? status;

  return (
    <span
      title={date ? `Status since ${date}` : label}
      className={cn("inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold cursor-default", colorClass)}
    >
      {label}
    </span>
  );
}
