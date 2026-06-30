"use client";
import { Pill } from "lucide-react";

export default function RxPage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center gap-3">
      <div className="w-12 h-12 rounded-xl bg-green-50 flex items-center justify-center">
        <Pill className="w-6 h-6 text-green-400" />
      </div>
      <p className="text-sm font-medium text-gray-700">Prescriptions — Coming in Phase 4</p>
      <p className="text-xs text-gray-400 max-w-xs">
        Active medications, renewal workflows, DrugRef2 formulary search, allergy cross-check, and eRx will appear here.
      </p>
    </div>
  );
}
