/**
 * Patient shell layout — fetches banner server-side and renders it sticky.
 * All patient sub-pages (summary, profile, contacts, consent) render as {children}.
 */
import { requireSession, getAccessToken } from "@/lib/auth";
import { fetchPatientBanner } from "@/lib/api/patients.server";
import PatientBanner from "@/components/clinical/PatientBanner/PatientBanner";
import { notFound } from "next/navigation";
import PatientNav from "@/components/clinical/PatientNav";

export default async function PatientLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { demographicNo: string };
}) {
  const session = await requireSession();
  const no = parseInt(params.demographicNo, 10);
  if (isNaN(no)) notFound();

  let token: string;
  try { token = getAccessToken(session); } catch { notFound(); return null; }

  let banner = null;
  try {
    banner = await fetchPatientBanner(token, no);
  } catch {
    // Banner fetch failed — render page without banner rather than 404ing
  }

  return (
    <div className="flex flex-col min-h-full -m-6">
      {banner && <PatientBanner banner={banner} />}
      <PatientNav base={`/patients/${no}`} />
      <div className="flex-1 p-6">{children}</div>
    </div>
  );
}
