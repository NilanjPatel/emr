import { requireSession } from "@/lib/auth";
import Sidebar from "@/components/clinical/Sidebar";
import TopBar from "@/components/clinical/TopBar";
import CommandPalette from "@/components/clinical/CommandPalette";

export default async function ClinicalLayout({ children }: { children: React.ReactNode }) {
  const session = await requireSession();

  return (
    <CommandPalette>
      <div className="flex h-screen overflow-hidden bg-gray-50">
        <Sidebar session={session} />
        <div className="flex flex-col flex-1 min-w-0 overflow-hidden">
          <TopBar session={session} />
          <main className="flex-1 overflow-y-auto p-6">
            {children}
          </main>
        </div>
      </div>
    </CommandPalette>
  );
}
