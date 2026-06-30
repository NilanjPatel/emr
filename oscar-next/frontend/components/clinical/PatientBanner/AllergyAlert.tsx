"use client";
import { useState } from "react";
import { AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";

interface Props {
  allergyCount: number;
  critical: boolean;
}

export default function AllergyAlert({ allergyCount, critical }: Props) {
  const [open, setOpen] = useState(false);

  if (allergyCount === 0) {
    return (
      <span className="text-xs text-gray-400 px-2 py-0.5 rounded-full border border-gray-200">
        No known allergies
      </span>
    );
  }

  return (
    <div className="relative inline-block">
      <button
        onMouseEnter={() => setOpen(true)}
        onMouseLeave={() => setOpen(false)}
        onClick={() => setOpen(v => !v)}
        aria-label={`${allergyCount} allerg${allergyCount === 1 ? "y" : "ies"} on file`}
        className={cn(
          "inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-semibold border cursor-pointer transition-colors",
          critical
            ? "bg-red-100 text-red-800 border-red-300 hover:bg-red-200"
            : "bg-amber-100 text-amber-800 border-amber-300 hover:bg-amber-200"
        )}
      >
        <AlertTriangle className="w-3 h-3" />
        {allergyCount} {allergyCount === 1 ? "Allergy" : "Allergies"}
      </button>

      {open && (
        <div className="absolute top-full mt-1 left-0 z-50 w-56 bg-white rounded-lg shadow-lg border border-gray-200 p-3 text-xs text-gray-700">
          <p className="font-semibold text-red-700 mb-1">
            {allergyCount} allerg{allergyCount === 1 ? "y" : "ies"} on file
          </p>
          <p className="text-gray-500">Open the Allergies tab to view details.</p>
        </div>
      )}
    </div>
  );
}
