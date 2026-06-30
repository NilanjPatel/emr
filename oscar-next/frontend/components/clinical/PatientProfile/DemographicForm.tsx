"use client";
import { useState, useEffect, useCallback } from "react";
import { Check, Loader2, ChevronDown, ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import type { PatientDetail, PatientUpdate } from "@/lib/types/patient";

// ── Sub-components ────────────────────────────────────────────────────────────

function Section({
  id,
  title,
  open,
  onToggle,
  children,
}: {
  id: string;
  title: string;
  open: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div id={id} className="border border-gray-200 rounded-xl overflow-hidden scroll-mt-28">
      <button
        type="button"
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-50 hover:bg-gray-100 text-sm font-semibold text-gray-700"
      >
        {title}
        {open ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
      </button>
      {open && <div className="px-4 py-4 grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">{children}</div>}
    </div>
  );
}

function Field({
  label,
  error,
  children,
  span2 = false,
}: {
  label: string;
  error?: string;
  children: React.ReactNode;
  span2?: boolean;
}) {
  return (
    <div className={cn("flex flex-col gap-1", span2 && "sm:col-span-2")}>
      <label className="text-xs font-medium text-gray-600">{label}</label>
      {children}
      {error && <p className="text-xs text-red-600">{error}</p>}
    </div>
  );
}

function Input({
  className,
  hasError,
  ...props
}: React.InputHTMLAttributes<HTMLInputElement> & { hasError?: boolean }) {
  return (
    <input
      className={cn(
        "h-9 px-3 text-sm rounded-lg border bg-white transition-colors outline-none",
        "focus:border-blue-400 focus:ring-2 focus:ring-blue-100",
        hasError ? "border-red-400" : "border-gray-200 hover:border-gray-300",
        className
      )}
      {...props}
    />
  );
}

function Sel({
  hasError,
  children,
  className,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement> & { hasError?: boolean }) {
  return (
    <select
      className={cn(
        "h-9 px-3 text-sm rounded-lg border bg-white transition-colors outline-none cursor-pointer",
        "focus:border-blue-400 focus:ring-2 focus:ring-blue-100",
        hasError ? "border-red-400" : "border-gray-200 hover:border-gray-300",
        className
      )}
      {...props}
    >
      {children}
    </select>
  );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

const ALWAYS_OPEN = new Set([
  "section-personal",
  "section-contact",
  "section-health",
  "section-provider",
]);

function splitDob(dob_iso?: string | null) {
  if (!dob_iso) return { year: "", month: "", day: "" };
  const [year = "", month = "", day = ""] = dob_iso.split("-");
  return { year, month, day };
}

function initState(p: PatientDetail) {
  const dob = splitDob(p.dob_iso);
  return {
    title:               p.title ?? "",
    first_name:          p.first_name ?? "",
    last_name:           p.last_name ?? "",
    middle_names:        p.middle_names ?? "",
    alias:               p.alias ?? "",
    pref_name:           p.pref_name ?? "",
    sex:                 p.sex ?? "U",
    year_of_birth:       dob.year,
    month_of_birth:      dob.month,
    date_of_birth:       dob.day,
    phone:               p.phone ?? "",
    phone2:              p.phone2 ?? "",
    email:               p.email ?? "",
    address:             p.address ?? "",
    city:                p.city ?? "",
    province:            p.province ?? "",
    postal:              p.postal ?? "",
    residentialAddress:  p.residentialAddress ?? "",
    residentialCity:     p.residentialCity ?? "",
    residentialProvince: p.residentialProvince ?? "",
    residentialPostal:   p.residentialPostal ?? "",
    hin:                 p.hin ?? "",
    ver:                 p.ver ?? "",
    hc_type:             p.hc_type ?? "",
    hc_renew_date:       p.hc_renew_date ?? "",
    chart_no:            p.chart_no ?? "",
    provider_no:         p.provider_no ?? "",
    official_lang:       p.official_lang ?? "",
    spoken_lang:         p.spoken_lang ?? "",
    citizenship:         p.citizenship ?? "",
    roster_status:       p.roster_status ?? "",
    patient_status:      p.patient_status ?? "AC",
  };
}

type FormState = ReturnType<typeof initState>;

// ── Main component ────────────────────────────────────────────────────────────

interface Props {
  patient: PatientDetail;
  onSave: (values: PatientUpdate) => Promise<void>;
  readonly?: boolean;
}

export default function DemographicForm({ patient, onSave, readonly = false }: Props) {
  const [fields, setFields] = useState<FormState>(() => initState(patient));
  const [errors, setErrors] = useState<Partial<Record<keyof FormState, string>>>({});
  const [saving, setSaving]   = useState(false);
  const [saved,  setSaved]    = useState(false);
  const [dirty,  setDirty]    = useState(false);

  // Lifted open-state so hash navigation can force-open collapsed sections
  const [openSections, setOpenSections] = useState<Set<string>>(new Set(ALWAYS_OPEN));

  const toggleSection = useCallback((id: string) => {
    setOpenSections(prev => {
      const arr = Array.from(prev);
      if (prev.has(id)) return new Set(arr.filter(x => x !== id));
      return new Set(arr.concat(id));
    });
  }, []);

  // On mount: read URL hash, open matching section, scroll to it
  useEffect(() => {
    const hash = window.location.hash.slice(1); // strip leading #
    if (!hash) return;
    setOpenSections(prev => new Set(Array.from(prev).concat(hash)));
    requestAnimationFrame(() => {
      document.getElementById(hash)?.scrollIntoView({ behavior: "smooth", block: "start" });
    });
  }, []);

  function set(key: keyof FormState, value: string) {
    setFields(prev => ({ ...prev, [key]: value }));
    setDirty(true);
    if (errors[key]) setErrors(prev => ({ ...prev, [key]: undefined }));
  }

  function validate(): boolean {
    const errs: Partial<Record<keyof FormState, string>> = {};
    if (!fields.first_name.trim()) errs.first_name = "Required";
    if (!fields.last_name.trim())  errs.last_name  = "Required";
    if (!["M","F","O","U","T","I"].includes(fields.sex)) errs.sex = "Select a valid sex";
    if (fields.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email))
      errs.email = "Invalid email";
    if (fields.postal && !/^[A-Za-z]\d[A-Za-z]\s?\d[A-Za-z]\d$/.test(fields.postal))
      errs.postal = "Use format A1A 1A1";
    if (fields.year_of_birth && !/^\d{4}$/.test(fields.year_of_birth))
      errs.year_of_birth = "4-digit year";
    setErrors(errs);
    return Object.keys(errs).length === 0;
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (readonly || !validate()) return;
    setSaving(true);
    try {
      const payload: PatientUpdate = {
        title:               fields.title     || undefined,
        first_name:          fields.first_name,
        last_name:           fields.last_name,
        middle_names:        fields.middle_names || undefined,
        alias:               fields.alias     || undefined,
        pref_name:           fields.pref_name || undefined,
        sex:                 fields.sex as PatientUpdate["sex"],
        year_of_birth:       fields.year_of_birth  || undefined,
        month_of_birth:      fields.month_of_birth || undefined,
        date_of_birth:       fields.date_of_birth  || undefined,
        phone:               fields.phone  || undefined,
        phone2:              fields.phone2 || undefined,
        email:               fields.email  || undefined,
        address:             fields.address   || undefined,
        city:                fields.city      || undefined,
        province:            fields.province  || undefined,
        postal:              fields.postal    || undefined,
        residentialAddress:  fields.residentialAddress  || undefined,
        residentialCity:     fields.residentialCity     || undefined,
        residentialProvince: fields.residentialProvince || undefined,
        residentialPostal:   fields.residentialPostal   || undefined,
        hin:          fields.hin         || undefined,
        ver:          fields.ver         || undefined,
        hc_type:      fields.hc_type     || undefined,
        hc_renew_date: fields.hc_renew_date || undefined,
        chart_no:     fields.chart_no    || undefined,
        provider_no:  fields.provider_no || undefined,
        official_lang: fields.official_lang || undefined,
        spoken_lang:   fields.spoken_lang   || undefined,
        citizenship:   fields.citizenship   || undefined,
        roster_status: fields.roster_status || undefined,
        patient_status: fields.patient_status || undefined,
      };
      await onSave(payload);
      setSaved(true);
      setDirty(false);
      setTimeout(() => setSaved(false), 2000);
    } finally {
      setSaving(false);
    }
  }

  const f = fields;

  return (
    <form onSubmit={handleSubmit} className="flex flex-col gap-4">

      {/* Personal */}
      <Section id="section-personal" title="Personal Information"
        open={openSections.has("section-personal")} onToggle={() => toggleSection("section-personal")}>
        <Field label="Title">
          <Input value={f.title} onChange={e => set("title", e.target.value)}
            placeholder="Dr / Mr / Ms…" disabled={readonly} />
        </Field>
        <Field label="First Name *" error={errors.first_name}>
          <Input value={f.first_name} onChange={e => set("first_name", e.target.value)}
            disabled={readonly} hasError={!!errors.first_name} />
        </Field>
        <Field label="Last Name *" error={errors.last_name}>
          <Input value={f.last_name} onChange={e => set("last_name", e.target.value)}
            disabled={readonly} hasError={!!errors.last_name} />
        </Field>
        <Field label="Middle Name(s)">
          <Input value={f.middle_names} onChange={e => set("middle_names", e.target.value)}
            disabled={readonly} />
        </Field>
        <Field label="Preferred Name">
          <Input value={f.pref_name} onChange={e => set("pref_name", e.target.value)}
            placeholder="Nickname / preferred" disabled={readonly} />
        </Field>
        <Field label="Alias">
          <Input value={f.alias} onChange={e => set("alias", e.target.value)}
            disabled={readonly} />
        </Field>
        <Field label="Sex *" error={errors.sex}>
          <Sel value={f.sex} onChange={e => set("sex", e.target.value)}
            disabled={readonly} hasError={!!errors.sex}>
            <option value="M">Male</option>
            <option value="F">Female</option>
            <option value="O">Other</option>
            <option value="U">Unknown</option>
            <option value="T">Transgender</option>
            <option value="I">Intersex</option>
          </Sel>
        </Field>
        <div className="flex flex-col gap-1">
          <label className="text-xs font-medium text-gray-600">Date of Birth</label>
          <div className="flex gap-2">
            <Input value={f.year_of_birth}  onChange={e => set("year_of_birth",  e.target.value)}
              placeholder="YYYY" className="w-20 text-center" disabled={readonly}
              hasError={!!errors.year_of_birth} />
            <Input value={f.month_of_birth} onChange={e => set("month_of_birth", e.target.value)}
              placeholder="MM" className="w-16 text-center" disabled={readonly} />
            <Input value={f.date_of_birth}  onChange={e => set("date_of_birth",  e.target.value)}
              placeholder="DD" className="w-16 text-center" disabled={readonly} />
          </div>
          {errors.year_of_birth && <p className="text-xs text-red-600">{errors.year_of_birth}</p>}
        </div>
        <Field label="Chart No.">
          <Input value={f.chart_no} onChange={e => set("chart_no", e.target.value)}
            disabled={readonly} />
        </Field>
      </Section>

      {/* Contact */}
      <Section id="section-contact" title="Contact Information"
        open={openSections.has("section-contact")} onToggle={() => toggleSection("section-contact")}>
        <Field label="Phone (Home)">
          <Input value={f.phone} onChange={e => set("phone", e.target.value)}
            type="tel" placeholder="416-555-0000" disabled={readonly} />
        </Field>
        <Field label="Phone (Mobile)">
          <Input value={f.phone2} onChange={e => set("phone2", e.target.value)}
            type="tel" placeholder="416-555-0000" disabled={readonly} />
        </Field>
        <Field label="Email" error={errors.email}>
          <Input value={f.email} onChange={e => set("email", e.target.value)}
            type="email" disabled={readonly} hasError={!!errors.email} />
        </Field>
        <Field label="Mailing Address" span2>
          <Input value={f.address} onChange={e => set("address", e.target.value)}
            placeholder="Street address" disabled={readonly} />
        </Field>
        <Field label="City">
          <Input value={f.city} onChange={e => set("city", e.target.value)}
            disabled={readonly} />
        </Field>
        <Field label="Province">
          <Input value={f.province} onChange={e => set("province", e.target.value)}
            maxLength={10} placeholder="ON" disabled={readonly} />
        </Field>
        <Field label="Postal Code" error={errors.postal}>
          <Input value={f.postal} onChange={e => set("postal", e.target.value)}
            placeholder="A1A 1A1" maxLength={7} disabled={readonly} hasError={!!errors.postal} />
        </Field>
      </Section>

      {/* Residential */}
      <Section id="section-address" title="Residential Address"
        open={openSections.has("section-address")} onToggle={() => toggleSection("section-address")}>
        <Field label="Residential Address" span2>
          <Input value={f.residentialAddress} onChange={e => set("residentialAddress", e.target.value)}
            disabled={readonly} />
        </Field>
        <Field label="City">
          <Input value={f.residentialCity} onChange={e => set("residentialCity", e.target.value)}
            disabled={readonly} />
        </Field>
        <Field label="Province">
          <Input value={f.residentialProvince} onChange={e => set("residentialProvince", e.target.value)}
            maxLength={10} placeholder="ON" disabled={readonly} />
        </Field>
        <Field label="Postal">
          <Input value={f.residentialPostal} onChange={e => set("residentialPostal", e.target.value)}
            maxLength={7} disabled={readonly} />
        </Field>
      </Section>

      {/* Health Card */}
      <Section id="section-health" title="Health Card"
        open={openSections.has("section-health")} onToggle={() => toggleSection("section-health")}>
        <Field label="HIN">
          <Input value={f.hin} onChange={e => set("hin", e.target.value)}
            maxLength={20} disabled={readonly} />
        </Field>
        <Field label="Version Code">
          <Input value={f.ver} onChange={e => set("ver", e.target.value)}
            maxLength={3} className="w-20" disabled={readonly} />
        </Field>
        <Field label="Province/Type">
          <Input value={f.hc_type} onChange={e => set("hc_type", e.target.value)}
            maxLength={20} placeholder="ON" disabled={readonly} />
        </Field>
        <Field label="Renewal Date">
          <Input value={f.hc_renew_date} onChange={e => set("hc_renew_date", e.target.value)}
            type="date" disabled={readonly} />
        </Field>
      </Section>

      {/* Provider / Enrolment */}
      <Section id="section-provider" title="Provider & Enrolment"
        open={openSections.has("section-provider")} onToggle={() => toggleSection("section-provider")}>
        <Field label="Provider No.">
          <Input value={f.provider_no} onChange={e => set("provider_no", e.target.value)}
            disabled={readonly} />
        </Field>
        <Field label="Roster Status">
          <Sel value={f.roster_status} onChange={e => set("roster_status", e.target.value)}
            disabled={readonly}>
            <option value="">—</option>
            <option value="RO">Rostered (RO)</option>
            <option value="TO">Temporarily Off (TO)</option>
            <option value="NR">Not Rostered (NR)</option>
          </Sel>
        </Field>
        <Field label="Patient Status">
          <Sel value={f.patient_status} onChange={e => set("patient_status", e.target.value)}
            disabled={readonly}>
            <option value="AC">Active</option>
            <option value="IN">Inactive</option>
            <option value="DE">Deceased</option>
            <option value="MO">Moved Out</option>
            <option value="NE">Newborn</option>
            <option value="SP">Suspended</option>
          </Sel>
        </Field>
      </Section>

      {/* Language / Other */}
      <Section id="section-lang" title="Language & Demographics"
        open={openSections.has("section-lang")} onToggle={() => toggleSection("section-lang")}>
        <Field label="Official Language">
          <Sel value={f.official_lang} onChange={e => set("official_lang", e.target.value)}
            disabled={readonly}>
            <option value="">—</option>
            <option value="English">English</option>
            <option value="French">French</option>
          </Sel>
        </Field>
        <Field label="Spoken Language">
          <Input value={f.spoken_lang} onChange={e => set("spoken_lang", e.target.value)}
            disabled={readonly} />
        </Field>
        <Field label="Citizenship">
          <Input value={f.citizenship} onChange={e => set("citizenship", e.target.value)}
            disabled={readonly} />
        </Field>
      </Section>

      {/* Save bar */}
      {!readonly && dirty && (
        <div className="sticky bottom-0 bg-white border-t border-gray-200 px-4 py-3 flex items-center justify-between rounded-b-xl">
          <p className="text-xs text-gray-500">Unsaved changes</p>
          <button
            type="submit"
            disabled={saving}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-60 transition-colors"
          >
            {saving ? <Loader2 className="w-4 h-4 animate-spin" /> : saved ? <Check className="w-4 h-4" /> : null}
            {saving ? "Saving…" : saved ? "Saved!" : "Save changes"}
          </button>
        </div>
      )}
    </form>
  );
}
