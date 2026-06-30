"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import type { Session } from "next-auth";
import {
  CalendarDays, Users, FileText, Pill, FlaskConical,
  Receipt, Inbox, Settings, Activity,
} from "lucide-react";

const NAV = [
  { href: "/schedule",  label: "Schedule",      icon: CalendarDays, keys: "F1" },
  { href: "/patients",  label: "Patients",       icon: Users,        keys: "F2" },
  { href: "/inbox",     label: "Inbox",          icon: Inbox,        keys: "F3" },
  { href: "/encounters",label: "Encounters",     icon: FileText,     keys: "F4" },
  { href: "/rx",        label: "Prescriptions",  icon: Pill,         keys: "F5" },
  { href: "/labs",      label: "Labs",           icon: FlaskConical, keys: "F6" },
  { href: "/billing",   label: "Billing",        icon: Receipt,      keys: "F7" },
];

export default function Sidebar({ session }: { session: Session }) {
  const pathname = usePathname();

  return (
    <aside className="hidden md:flex w-56 flex-col bg-white border-r border-gray-200 py-4">
      <div className="px-4 mb-6 flex items-center gap-2">
        <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
          <Activity className="w-4 h-4 text-white" />
        </div>
        <span className="font-semibold text-gray-900 text-sm">Oscar EMR</span>
      </div>

      <nav className="flex-1 px-2 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon, keys }) => {
          const active = pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center justify-between gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors group",
                active
                  ? "bg-blue-50 text-blue-700"
                  : "text-gray-600 hover:bg-gray-100 hover:text-gray-900"
              )}
            >
              <span className="flex items-center gap-3">
                <Icon className="w-4 h-4 flex-shrink-0" />
                {label}
              </span>
              <kbd className="hidden group-hover:inline text-[10px] text-gray-400 font-mono">
                {keys}
              </kbd>
            </Link>
          );
        })}
      </nav>

      <div className="px-2 mt-4 border-t border-gray-100 pt-4 space-y-0.5">
        <Link
          href="/admin"
          className="flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:bg-gray-100 hover:text-gray-900 transition-colors"
        >
          <Settings className="w-4 h-4" />
          Admin
        </Link>
        <div className="px-3 py-2">
          <p className="text-xs font-medium text-gray-900 truncate">
            {session?.user?.name ?? session?.user?.email ?? "Provider"}
          </p>
          <p className="text-[10px] text-gray-400 truncate">
            {session?.user?.roles?.join(", ") ?? ""}
          </p>
        </div>
      </div>
    </aside>
  );
}
