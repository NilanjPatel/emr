"use client";
import { FlaskConical } from "lucide-react";

export default function LabsPage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center gap-3">
      <div className="w-12 h-12 rounded-xl bg-purple-50 flex items-center justify-center">
        <FlaskConical className="w-6 h-6 text-purple-400" />
      </div>
      <p className="text-sm font-medium text-gray-700">Labs — Coming in Phase 4</p>
      <p className="text-xs text-gray-400 max-w-xs">
        Inbound HL7 lab results, trend sparklines, critical value flags, and diagnostic reports will appear here.
      </p>
    </div>
  );
}
