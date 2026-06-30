"use client";
import { Phone, Mail, User } from "lucide-react";
import type { PatientContact } from "@/lib/types/patient";
import { cn } from "@/lib/utils";

const ROLE_LABELS: Record<string, string> = {
  EC: "Emergency Contact",
  SDM: "Substitute Decision Maker",
  MRP: "Most Responsible Provider",
  HCT: "Health Care Team",
};

function Badge({ label, active }: { label: string; active: boolean }) {
  return active ? (
    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-blue-100 text-blue-700">
      {label}
    </span>
  ) : null;
}

export default function ContactCard({ link }: { link: PatientContact }) {
  const c = link.contact;
  const name = c ? `${c.firstName ?? ""} ${c.lastName ?? ""}`.trim() : `Contact ${link.contactId}`;
  const role = ROLE_LABELS[link.role ?? ""] ?? link.role;

  return (
    <div className={cn("p-4 rounded-xl border bg-white", link.active === 0 ? "opacity-50" : "")}>
      <div className="flex items-start justify-between gap-2">
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-gray-100 flex items-center justify-center">
            <User className="w-4 h-4 text-gray-400" />
          </div>
          <div>
            <p className="text-sm font-semibold text-gray-900">{name || "—"}</p>
            {role && <p className="text-xs text-gray-500">{role}</p>}
          </div>
        </div>
        <div className="flex items-center gap-1 flex-wrap justify-end">
          <Badge label="EC"  active={link.ec === "Y"} />
          <Badge label="SDM" active={link.sdm === "Y"} />
          <Badge label="MRP" active={!!link.mrp} />
          <Badge label="HCT" active={!!link.health_care_team} />
        </div>
      </div>

      {c && (
        <div className="mt-3 flex flex-col gap-1 text-xs text-gray-600">
          {(c.residencePhone || c.cellPhone || c.workPhone) && (
            <div className="flex items-center gap-1.5">
              <Phone className="w-3 h-3 text-gray-400" />
              <span>
                {[c.residencePhone, c.cellPhone, c.workPhone].filter(Boolean).join(" · ")}
              </span>
            </div>
          )}
          {c.email && (
            <div className="flex items-center gap-1.5">
              <Mail className="w-3 h-3 text-gray-400" />
              <a href={`mailto:${c.email}`} className="hover:underline text-blue-600">{c.email}</a>
            </div>
          )}
          {(c.city || c.province) && (
            <p className="text-gray-500">
              {[c.address, c.city, c.province, c.postal].filter(Boolean).join(", ")}
            </p>
          )}
          {link.note && (
            <p className="mt-1 text-gray-500 italic">{link.note}</p>
          )}
        </div>
      )}
    </div>
  );
}
