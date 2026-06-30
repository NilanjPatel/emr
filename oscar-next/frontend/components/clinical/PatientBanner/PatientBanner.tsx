"use client";
import { Pill, User } from "lucide-react";
import PatientStatusChip from "./PatientStatusChip";
import AllergyAlert from "./AllergyAlert";
import type { PatientBanner as PatientBannerData } from "@/lib/types/patient";
import { formatDate } from "@/lib/utils";

interface Props {
  banner: PatientBannerData;
}

function Dot() {
  return <span className="text-gray-300 select-none">·</span>;
}

function HINBadge({ hin, hcType, renewDate }: { hin?: string | null; hcType?: string | null; renewDate?: string | null }) {
  if (!hin) return null;

  let status: "ok" | "expiring" | "expired" = "ok";
  if (renewDate) {
    const exp = new Date(renewDate);
    const daysLeft = (exp.getTime() - Date.now()) / (1000 * 60 * 60 * 24);
    if (daysLeft < 0) status = "expired";
    else if (daysLeft < 30) status = "expiring";
  }

  return (
    <span
      title={renewDate ? `Expires ${renewDate}` : undefined}
      className={
        status === "expired"   ? "text-red-600 font-medium" :
        status === "expiring"  ? "text-amber-600 font-medium" :
        "text-gray-700"
      }
    >
      {hcType ? `${hcType} ` : ""}{hin}
      {status === "expiring" && <span className="ml-1 text-[10px] bg-amber-100 text-amber-700 px-1 py-0.5 rounded">Exp Soon</span>}
      {status === "expired"  && <span className="ml-1 text-[10px] bg-red-100  text-red-700  px-1 py-0.5 rounded">Expired</span>}
    </span>
  );
}

export default function PatientBanner({ banner }: Props) {
  const initials = banner.display_name
    .split(",")
    .map(s => s.trim()[0] ?? "")
    .reverse()
    .join("")
    .toUpperCase()
    .slice(0, 2);

  const today = new Date();
  const isBirthday = banner.dob_iso
    ? banner.dob_iso.slice(5) === `${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`
    : false;

  return (
    <div className="sticky top-0 z-40 h-14 bg-white border-b border-gray-200 shadow-sm">
      <div className="px-6 h-full flex items-center gap-4">
        {/* Avatar */}
        <div className="w-10 h-10 rounded-full bg-blue-600 text-white flex items-center justify-center text-sm font-bold flex-shrink-0">
          {initials || <User className="w-5 h-5" />}
        </div>

        {/* Name + meta */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <h1 className="text-base font-semibold text-gray-900">
              {banner.display_name}
              {isBirthday && <span className="ml-1" title="Birthday today!">🎂</span>}
            </h1>
            {banner.pref_name && (
              <span className="text-sm text-gray-500">({banner.pref_name})</span>
            )}
            <PatientStatusChip status={banner.patient_status} date={undefined} />
          </div>

          <div className="flex items-center gap-2 text-xs text-gray-500 flex-wrap mt-0.5">
            {banner.dob_iso && (
              <>
                <span>DOB: {formatDate(banner.dob_iso)}</span>
                {banner.age != null && (
                  <><Dot /><span>{banner.age}y</span></>
                )}
              </>
            )}
            {banner.sex && (
              <><Dot /><span>{banner.sex}</span></>
            )}
            {banner.hin && (
              <><Dot />
                <HINBadge hin={banner.hin} hcType={banner.hc_type} renewDate={banner.hc_renew_date} />
              </>
            )}
            {banner.chart_no && (
              <><Dot /><span>Chart: {banner.chart_no}</span></>
            )}
            {banner.provider_no && (
              <><Dot /><span>Dr {banner.provider_no}</span></>
            )}
          </div>
        </div>

        {/* Right: allergy + Rx chips */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <AllergyAlert allergyCount={banner.allergy_count} critical={banner.critical_allergy} />

          {banner.active_rx_count > 0 && (
            <span
              title={`${banner.active_rx_count} active prescription${banner.active_rx_count === 1 ? "" : "s"}`}
              className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800 border border-purple-200"
            >
              <Pill className="w-3 h-3" />
              {banner.active_rx_count} Rx
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
