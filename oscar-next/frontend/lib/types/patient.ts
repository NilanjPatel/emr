// Patient types — mirrors backend Pydantic schemas.
// SIN is intentionally absent from all types: it is never returned by the API.

export interface PatientSearchResult {
  demographic_no: number;
  first_name: string;
  last_name: string;
  pref_name?: string | null;
  dob_iso?: string | null;
  age?: number | null;
  hin?: string | null;
  chart_no?: string | null;
  patient_status?: string | null;
  patient_status_label?: string | null;
  provider_no?: string | null;
}

export interface PatientSearchResponse {
  total: number;
  page: number;
  limit: number;
  results: PatientSearchResult[];
}

export interface PatientBanner {
  demographic_no: number;
  display_name: string;
  pref_name?: string | null;
  dob_iso?: string | null;
  age?: number | null;
  sex?: string | null;
  hin?: string | null;
  hc_type?: string | null;
  hc_renew_date?: string | null;
  chart_no?: string | null;
  patient_status?: string | null;
  patient_status_label?: string | null;
  allergy_count: number;
  critical_allergy: boolean;
  active_rx_count: number;
  provider_no?: string | null;
  roster_status?: string | null;
}

export interface PatientDetail {
  demographic_no: number;
  title?: string | null;
  first_name: string;
  last_name: string;
  middle_names?: string | null;
  alias?: string | null;
  pref_name?: string | null;
  sex: string;
  dob_iso?: string | null;
  age?: number | null;
  phone?: string | null;
  phone2?: string | null;
  email?: string | null;
  consentToUseEmailForCare?: number | null;
  address?: string | null;
  city?: string | null;
  province?: string | null;
  postal?: string | null;
  previousAddress?: string | null;
  residentialAddress?: string | null;
  residentialCity?: string | null;
  residentialProvince?: string | null;
  residentialPostal?: string | null;
  hin?: string | null;
  ver?: string | null;
  hc_type?: string | null;
  hc_renew_date?: string | null;
  roster_status?: string | null;
  roster_date?: string | null;
  roster_termination_date?: string | null;
  roster_termination_reason?: string | null;
  roster_enrolled_to?: string | null;
  patient_status?: string | null;
  patient_status_label?: string | null;
  patient_status_date?: string | null;
  date_joined?: string | null;
  end_date?: string | null;
  provider_no?: string | null;
  family_doctor?: string | null;
  family_physician?: string | null;
  chart_no?: string | null;
  official_lang?: string | null;
  spoken_lang?: string | null;
  citizenship?: string | null;
  country_of_origin?: string | null;
  pcn_indicator?: string | null;
  anonymous?: string | null;
  newsletter?: string | null;
  children?: string | null;
  sourceOfIncome?: string | null;
  myOscarUserName?: string | null;
  lastUpdateUser?: string | null;
  lastUpdateDate?: string | null;
}

export interface PatientCreate {
  first_name: string;
  last_name: string;
  sex: string;
  year_of_birth?: string;
  month_of_birth?: string;
  date_of_birth?: string;
  title?: string;
  middle_names?: string;
  alias?: string;
  pref_name?: string;
  phone?: string;
  phone2?: string;
  email?: string;
  consentToUseEmailForCare?: number;
  address?: string;
  city?: string;
  province?: string;
  postal?: string;
  residentialAddress?: string;
  residentialCity?: string;
  residentialProvince?: string;
  residentialPostal?: string;
  hin?: string;
  ver?: string;
  hc_type?: string;
  hc_renew_date?: string;
  roster_status?: string;
  provider_no?: string;
  chart_no?: string;
  official_lang?: string;
  spoken_lang?: string;
  citizenship?: string;
  patient_status?: string;
}

export type PatientUpdate = Partial<PatientCreate>;

export interface DuplicateCandidate {
  demographic_no: number;
  first_name: string;
  last_name: string;
  dob_iso?: string | null;
  hin?: string | null;
  chart_no?: string | null;
  patient_status?: string | null;
  score: number;
}

export interface DuplicateCheckResponse {
  has_duplicates: boolean;
  candidates: DuplicateCandidate[];
}

export interface ExtField {
  key_val?: string | null;
  value?: string | null;
  date_time?: string | null;
}

export interface ContactEntity {
  id: number;
  type?: string | null;
  firstName?: string | null;
  lastName?: string | null;
  residencePhone?: string | null;
  cellPhone?: string | null;
  workPhone?: string | null;
  email?: string | null;
  fax?: string | null;
  specialty?: string | null;
  address?: string | null;
  city?: string | null;
  province?: string | null;
  postal?: string | null;
}

export interface PatientContact {
  id: number;
  contactId?: string | null;
  role?: string | null;
  sdm?: string | null;
  ec?: string | null;
  mrp?: number | null;
  health_care_team?: number | null;
  best_contact?: string | null;
  category?: string | null;
  note?: string | null;
  active?: number | null;
  consentToContact?: number | null;
  contact?: ContactEntity | null;
}

export interface ConsentRecord {
  id: number;
  consent_type_id?: number | null;
  explicit?: number | null;
  optout?: number | null;
  last_entered_by?: string | null;
  consent_date?: string | null;
  optout_date?: string | null;
  edit_date?: string | null;
}

export interface MergeHistory {
  id: number;
  demographic_no: number;
  merged_to: number;
  deleted: number;
  lastUpdateUser?: string | null;
  lastUpdateDate?: string | null;
}

export const PATIENT_STATUS_COLORS: Record<string, string> = {
  AC: "bg-green-100 text-green-800",
  IN: "bg-gray-100 text-gray-700",
  DE: "bg-black text-white",
  MO: "bg-amber-100 text-amber-800",
  NE: "bg-blue-100 text-blue-800",
  SP: "bg-red-100 text-red-800",
};
