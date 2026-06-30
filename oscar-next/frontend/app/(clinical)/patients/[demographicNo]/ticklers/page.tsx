"use client";
import { Bell } from "lucide-react";

export default function TicklersPage() {
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center gap-3">
      <div className="w-12 h-12 rounded-xl bg-amber-50 flex items-center justify-center">
        <Bell className="w-6 h-6 text-amber-400" />
      </div>
      <p className="text-sm font-medium text-gray-700">Ticklers — Coming in Phase 3</p>
      <p className="text-xs text-gray-400 max-w-xs">
        Follow-up reminders, recall notices, and task assignments linked to this patient will appear here.
      </p>
    </div>
  );
}
