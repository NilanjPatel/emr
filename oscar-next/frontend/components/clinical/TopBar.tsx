"use client";
import { signOut } from "next-auth/react";
import { Search, LogOut, Bell } from "lucide-react";
import { useCommandPalette } from "./CommandPalette";
import type { Session } from "next-auth";

// eslint-disable-next-line @typescript-eslint/no-unused-vars
export default function TopBar({ session }: { session: Session }) {
  const { open } = useCommandPalette();

  return (
    <header className="h-14 bg-white border-b border-gray-200 flex items-center px-4 gap-4 flex-shrink-0">
      <button
        onClick={open}
        className="flex items-center gap-2 flex-1 max-w-sm px-3 py-1.5 rounded-lg bg-gray-100 hover:bg-gray-200 transition-colors text-sm text-gray-500 text-left"
      >
        <Search className="w-4 h-4 flex-shrink-0" />
        <span>Search patients, commands…</span>
        <kbd className="ml-auto text-[10px] font-mono text-gray-400">⌘K</kbd>
      </button>

      <div className="flex items-center gap-1 ml-auto">
        <button className="p-2 rounded-lg hover:bg-gray-100 transition-colors">
          <Bell className="w-4 h-4 text-gray-500" />
        </button>
        <button
          onClick={() => signOut({ callbackUrl: "/login" })}
          className="p-2 rounded-lg hover:bg-gray-100 transition-colors"
          title="Sign out"
        >
          <LogOut className="w-4 h-4 text-gray-500" />
        </button>
      </div>
    </header>
  );
}
