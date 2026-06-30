"use client";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { cn } from "@/lib/utils";
import type { KeyboardEvent } from "react";

const TABS = [
  { suffix: "",           label: "Summary",  key: "1" },
  { suffix: "/profile",   label: "Profile",  key: "2" },
  { suffix: "/contacts",  label: "Contacts", key: "3" },
  { suffix: "/consent",   label: "Consent",  key: "4" },
  { suffix: "/echart",    label: "eChart",   key: "5", stub: true },
  { suffix: "/rx",        label: "Rx",       key: "6", stub: true },
  { suffix: "/labs",      label: "Labs",     key: "7", stub: true },
  { suffix: "/ticklers",  label: "Ticklers", key: "8", stub: true },
];

export default function PatientNav({ base }: { base: string }) {
  const pathname = usePathname();
  const router   = useRouter();

  const activeIdx = TABS.findIndex(({ suffix }) =>
    suffix === "" ? pathname === base : pathname.startsWith(`${base}${suffix}`)
  );

  function tabHref(idx: number) {
    const suffix = TABS[idx].suffix;
    return suffix === "" ? base : `${base}${suffix}`;
  }

  function handleKeyDown(e: KeyboardEvent<HTMLElement>) {
    const count = TABS.length;

    if (e.key === "ArrowRight") {
      e.preventDefault();
      router.push(tabHref((activeIdx + 1) % count));
    } else if (e.key === "ArrowLeft") {
      e.preventDefault();
      router.push(tabHref((activeIdx - 1 + count) % count));
    } else if (e.key === "Home") {
      e.preventDefault();
      router.push(tabHref(0));
    } else if (e.key === "End") {
      e.preventDefault();
      router.push(tabHref(count - 1));
    }

    if (e.altKey && !e.ctrlKey && !e.metaKey) {
      const idx = TABS.findIndex(t => t.key === e.key);
      if (idx !== -1) {
        e.preventDefault();
        router.push(tabHref(idx));
      }
    }
  }

  return (
    <nav
      role="tablist"
      aria-label="Patient record sections"
      className="sticky top-14 z-30 bg-white border-b border-gray-200 px-6 overflow-x-auto"
      onKeyDown={handleKeyDown}
    >
      <div className="flex gap-0 min-w-max">
        {TABS.map(({ suffix, label, key, stub }, idx) => {
          const href   = suffix === "" ? base : `${base}${suffix}`;
          const active = idx === activeIdx;

          return (
            <Link
              key={suffix}
              href={href}
              role="tab"
              aria-selected={active}
              tabIndex={active ? 0 : -1}
              title={`${label} (Alt+${key})`}
              className={cn(
                "px-4 py-3 text-sm font-medium border-b-2 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500 focus-visible:ring-offset-1 whitespace-nowrap",
                active
                  ? "border-blue-600 text-blue-700"
                  : stub
                  ? "border-transparent text-gray-400 hover:text-gray-600 hover:border-gray-200"
                  : "border-transparent text-gray-600 hover:text-gray-900 hover:border-gray-300"
              )}
            >
              {label}
              {stub && (
                <span className="ml-1.5 text-[10px] font-normal text-gray-300 hidden sm:inline">soon</span>
              )}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
