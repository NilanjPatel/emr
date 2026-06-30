import { requireSession } from "@/lib/auth";

export default async function SchedulePage() {
  await requireSession();

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold text-gray-900">Today&apos;s Schedule</h1>
          <p className="text-sm text-gray-500 mt-0.5">
            {new Intl.DateTimeFormat("en-CA", { weekday: "long", year: "numeric", month: "long", day: "numeric" }).format(new Date())}
          </p>
        </div>
        <button className="px-4 py-2 rounded-lg bg-blue-600 text-white text-sm font-medium hover:bg-blue-700 transition-colors">
          + New Appointment
        </button>
      </div>

      {/* Schedule placeholder — replaced in Phase 1 */}
      <div className="bg-white rounded-2xl border border-gray-200 p-8 text-center">
        <div className="w-12 h-12 rounded-xl bg-blue-50 flex items-center justify-center mx-auto mb-3">
          <svg className="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
              d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
        </div>
        <p className="text-sm font-medium text-gray-700">Schedule module coming in Phase 1</p>
        <p className="text-xs text-gray-400 mt-1">FullCalendar multi-provider day view</p>
      </div>
    </div>
  );
}
