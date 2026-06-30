"use client";
import { FileText } from "lucide-react";

export default function EChartPage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center gap-3">
      <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center">
        <FileText className="w-6 h-6 text-blue-400" />
      </div>
      <p className="text-sm font-medium text-gray-700">eChart — Coming in Phase 3</p>
      <p className="text-xs text-gray-400 max-w-xs">
        Encounter notes, SOAP editor, Cumulative Patient Profile, vitals, and AI-assisted documentation will appear here.
      </p>
    </div>
  );
}
