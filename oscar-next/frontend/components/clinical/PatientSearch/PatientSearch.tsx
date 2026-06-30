"use client";
/**
 * PatientSearch — ⌘K patient lookup integrated into CommandPalette.
 *
 * Opens when the ⌘K CommandPalette is triggered AND the user starts typing a patient name,
 * HIN, or chart number. Returns a patient card list; click navigates to patient chart.
 *
 * Can also be used as a standalone inline component (e.g., in appointment booking modal).
 */
import { useState, useEffect, useCallback, useRef } from "react";
import { useRouter } from "next/navigation";
import { Search, Loader2 } from "lucide-react";
import { useSession } from "next-auth/react";
import { fetchPatientSearch } from "@/lib/api/patients";
import { getAccessToken } from "@/lib/auth";
import PatientSearchResult from "./PatientSearchResult";
import type { PatientSearchResult as PatientResultType } from "@/lib/types/patient";
import { cn } from "@/lib/utils";

interface Props {
  inline?: boolean;
  onSelect?: (patient: PatientResultType) => void;
  placeholder?: string;
  autoFocus?: boolean;
}

export default function PatientSearch({ inline = false, onSelect, placeholder, autoFocus = false }: Props) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<PatientResultType[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(0);
  const [showResults, setShowResults] = useState(false);
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const router = useRouter();
  const { data: session } = useSession();

  const doSearch = useCallback(async (q: string) => {
    if (q.trim().length < 2) {
      setResults([]);
      setShowResults(false);
      return;
    }
    let token: string;
    try { token = getAccessToken(session); } catch {
      setResults([]);
      setShowResults(false);
      return;
    }
    setLoading(true);
    try {
      const data = await fetchPatientSearch(token, { q: q.trim(), limit: 8 });
      setResults(data.results);
      setTotal(data.total);
      setSelected(0);
      setShowResults(true);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  }, [session]);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    if (!query.trim()) {
      setResults([]);
      setShowResults(false);
      return;
    }
    debounceRef.current = setTimeout(() => doSearch(query), 250);
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current); };
  }, [query, doSearch]);

  const handleSelect = useCallback((patient: PatientResultType) => {
    if (onSelect) {
      onSelect(patient);
    } else {
      router.push(`/patients/${patient.demographic_no}`);
    }
    setQuery("");
    setShowResults(false);
  }, [onSelect, router]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (!showResults || results.length === 0) return;
      if (e.key === "ArrowDown") { e.preventDefault(); setSelected(s => Math.min(s + 1, results.length - 1)); }
      if (e.key === "ArrowUp")   { e.preventDefault(); setSelected(s => Math.max(s - 1, 0)); }
      if (e.key === "Enter")     { e.preventDefault(); handleSelect(results[selected]); }
      if (e.key === "Escape")    { setShowResults(false); }
    };
    window.addEventListener("keydown", handler);
    return () => window.removeEventListener("keydown", handler);
  }, [showResults, results, selected, handleSelect]);

  return (
    <div className={cn("relative", inline ? "w-full" : "w-full max-w-lg")}>
      {/* Input */}
      <div className="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-lg bg-white focus-within:border-blue-400 focus-within:ring-2 focus-within:ring-blue-100">
        {loading
          ? <Loader2 className="w-4 h-4 text-gray-400 animate-spin flex-shrink-0" />
          : <Search className="w-4 h-4 text-gray-400 flex-shrink-0" />
        }
        <input
          autoFocus={autoFocus}
          value={query}
          onChange={e => setQuery(e.target.value)}
          onFocus={() => results.length > 0 && setShowResults(true)}
          placeholder={placeholder ?? "Search patient by name, HIN, chart #…"}
          className="flex-1 text-sm bg-transparent outline-none text-gray-900 placeholder:text-gray-400"
        />
        {query && (
          <button onClick={() => { setQuery(""); setShowResults(false); }}
            className="text-gray-400 hover:text-gray-600 text-xs">✕</button>
        )}
      </div>

      {/* Dropdown results */}
      {showResults && (
        <div className="absolute top-full mt-1 left-0 right-0 z-50 bg-white rounded-xl shadow-xl border border-gray-200 overflow-hidden">
          {results.length === 0 && !loading && (
            <p className="px-4 py-6 text-sm text-center text-gray-400">No patients found</p>
          )}
          <div className="max-h-72 overflow-y-auto divide-y divide-gray-50">
            {results.map((p, i) => (
              <PatientSearchResult
                key={p.demographic_no}
                patient={p}
                isSelected={i === selected}
                onSelect={handleSelect}
              />
            ))}
          </div>
          {total > results.length && (
            <div className="px-4 py-2 border-t border-gray-100 text-xs text-gray-400 text-center">
              {total - results.length} more results — refine your search
            </div>
          )}
        </div>
      )}
    </div>
  );
}
