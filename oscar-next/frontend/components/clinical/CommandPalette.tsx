"use client";
import { useEffect, useState, createContext, useContext, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Search, CalendarDays, Users, FileText, Pill, FlaskConical, Receipt, Settings } from "lucide-react";
import { cn } from "@/lib/utils";

type CommandPaletteContextType = { open: () => void; close: () => void };
const CommandPaletteContext = createContext<CommandPaletteContextType>({
  open: () => {},
  close: () => {},
});
export const useCommandPalette = () => useContext(CommandPaletteContext);

const COMMANDS = [
  { id: "schedule",    label: "Go to Schedule",      icon: CalendarDays, href: "/schedule" },
  { id: "patients",   label: "Go to Patients",       icon: Users,        href: "/patients" },
  { id: "new-patient",label: "New Patient",           icon: Users,        href: "/patients/new" },
  { id: "encounters", label: "Encounter Notes",       icon: FileText,     href: "/encounters" },
  { id: "rx",         label: "Prescriptions",         icon: Pill,         href: "/rx" },
  { id: "labs",       label: "Lab Results",           icon: FlaskConical, href: "/labs" },
  { id: "billing",    label: "Billing",               icon: Receipt,      href: "/billing" },
  { id: "admin",      label: "Admin Settings",        icon: Settings,     href: "/admin" },
];

export default function CommandPalette({ children }: { children?: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [selected, setSelected] = useState(0);
  const router = useRouter();

  const open = useCallback(() => { setIsOpen(true); setQuery(""); setSelected(0); }, []);
  const close = useCallback(() => setIsOpen(false), []);

  const filtered = COMMANDS.filter(c =>
    c.label.toLowerCase().includes(query.toLowerCase())
  );

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === "k") { e.preventDefault(); open(); }
      if (e.key === "Escape") close();
      // F1–F8 shortcuts
      const fKeys: Record<string, string> = {
        F1: "/schedule", F2: "/patients", F3: "/inbox",
        F4: "/encounters", F5: "/rx", F6: "/labs", F7: "/billing",
      };
      if (fKeys[e.key]) { e.preventDefault(); router.push(fKeys[e.key]); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [open, close, router]);

  useEffect(() => {
    if (!isOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === "ArrowDown") { e.preventDefault(); setSelected(s => Math.min(s + 1, filtered.length - 1)); }
      if (e.key === "ArrowUp")   { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
      if (e.key === "Enter" && filtered[selected]) {
        router.push(filtered[selected].href);
        close();
      }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [isOpen, filtered, selected, router, close]);

  return (
    <CommandPaletteContext.Provider value={{ open, close }}>
      {children}
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
          {/* Backdrop */}
          <div className="absolute inset-0 bg-black/40 backdrop-blur-sm" onClick={close} />

          {/* Panel */}
          <div className="relative w-full max-w-lg mx-4 bg-white rounded-2xl shadow-2xl border border-gray-200 overflow-hidden">
            {/* Input */}
            <div className="flex items-center gap-3 px-4 py-3 border-b border-gray-100">
              <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
              <input
                autoFocus
                value={query}
                onChange={e => { setQuery(e.target.value); setSelected(0); }}
                placeholder="Search patients, go to page, run command…"
                className="flex-1 text-sm bg-transparent outline-none text-gray-900 placeholder:text-gray-400"
              />
              <kbd className="text-xs font-mono text-gray-400 bg-gray-100 px-1.5 py-0.5 rounded">ESC</kbd>
            </div>

            {/* Results */}
            <div className="py-2 max-h-80 overflow-y-auto">
              {filtered.length === 0 && (
                <p className="px-4 py-6 text-sm text-center text-gray-400">No results</p>
              )}
              {filtered.map((cmd, i) => {
                const Icon = cmd.icon;
                return (
                  <button
                    key={cmd.id}
                    onClick={() => { router.push(cmd.href); close(); }}
                    onMouseEnter={() => setSelected(i)}
                    className={cn(
                      "w-full flex items-center gap-3 px-4 py-2.5 text-sm text-left transition-colors",
                      i === selected ? "bg-blue-50 text-blue-700" : "text-gray-700 hover:bg-gray-50"
                    )}
                  >
                    <Icon className="w-4 h-4 flex-shrink-0" />
                    {cmd.label}
                  </button>
                );
              })}
            </div>

            {/* Footer hints */}
            <div className="px-4 py-2 border-t border-gray-100 flex gap-4 text-[10px] text-gray-400">
              <span><kbd className="font-mono">↑↓</kbd> navigate</span>
              <span><kbd className="font-mono">↵</kbd> select</span>
              <span><kbd className="font-mono">F1–F7</kbd> quick nav</span>
            </div>
          </div>
        </div>
      )}
    </CommandPaletteContext.Provider>
  );
}
