// Issued employee letters, company policies and the letterhead printed
// on generated letters.
import { apiClient } from "./client";
import { API_BASE_URL } from "@/lib/constants";

const V1 = "/api/v1";
const MULTIPART = { headers: { "Content-Type": "multipart/form-data" } };

export const LETTER_TYPES = [
  "offer",
  "appointment",
  "confirmation",
  "increment",
  "promotion",
  "experience",
  "relieving",
  "termination",
  "warning",
  "other",
] as const;
export type LetterType = (typeof LETTER_TYPES)[number];

export const POLICY_CATEGORIES = [
  "hr",
  "leave",
  "attendance",
  "conduct",
  "it",
  "travel",
  "safety",
  "other",
] as const;
export type PolicyCategory = (typeof POLICY_CATEGORIES)[number];

export const letterTypeLabel = (t: string) =>
  ({
    offer: "Offer letter",
    appointment: "Appointment letter",
    confirmation: "Confirmation letter",
    increment: "Increment letter",
    promotion: "Promotion letter",
    experience: "Experience letter",
    relieving: "Relieving letter",
    termination: "Termination letter",
    warning: "Warning letter",
    other: "Other letter",
  })[t] ?? t;

export const policyCategoryLabel = (c: string) =>
  ({
    hr: "HR",
    leave: "Leave",
    attendance: "Attendance",
    conduct: "Code of conduct",
    it: "IT & security",
    travel: "Travel",
    safety: "Safety",
    other: "Other",
  })[c] ?? c;

export interface EmployeeLetter {
  id: number;
  employee_id: number;
  letter_type: LetterType;
  title: string;
  letter_number: string | null;
  issued_on: string;
  source: "generated" | "uploaded";
  template_id: number | null;
  file_name: string;
  mime_type: string;
  file_size: number | null;
  visible_to_employee: boolean;
  notes: string | null;
  issued_by: number | null;
  created_at: string | null;
}

export interface LetterIssuePayload {
  letter_type?: LetterType;
  title?: string;
  letter_no?: string;
  on_date?: string;
  last_working_date?: string;
  ctc_amount?: string;
  ctc_amount_words?: string;
  visible_to_employee: boolean;
  notes?: string;
}

export interface CompanyPolicy {
  id: number;
  title: string;
  category: PolicyCategory;
  description: string | null;
  version: string | null;
  effective_date: string | null;
  file_name: string;
  mime_type: string;
  file_size: number | null;
  is_published: boolean;
  requires_acknowledgement: boolean;
  revision: number;
  uploaded_by: number | null;
  created_at: string | null;
  updated_at: string | null;
  /** HR view: current staff who have / haven't accepted this version. */
  acknowledged_count: number | null;
  pending_count: number | null;
}

export interface PolicyAckRow {
  employee_id: number;
  employee_code: string;
  name: string;
  department: string | null;
  acknowledged_at: string | null;
}

export interface PolicyAckReport {
  policy_id: number;
  revision: number;
  acknowledged: PolicyAckRow[];
  pending: PolicyAckRow[];
}

export interface Letterhead {
  company_name: string;
  cin: string;
  gst: string;
  phone: string;
  email: string;
  website: string;
  regd_office: string;
  corporate_office: string;
  footer_note: string;
  show_watermark: boolean;
  show_corner_accents: boolean;
  has_custom_logo: boolean;
}
export type LetterheadUpdate = Partial<Omit<Letterhead, "has_custom_logo">>;

function form(fields: Record<string, string | number | boolean | null | undefined>, file?: File) {
  const fd = new FormData();
  for (const [k, v] of Object.entries(fields)) {
    if (v !== undefined && v !== null && v !== "") fd.append(k, String(v));
  }
  if (file) fd.append("file", file);
  return fd;
}

export const hrDocumentsApi = {
  // ── Employee letters ──────────────────────────────────────────────
  letters: async (employeeId: number) =>
    (await apiClient.get<EmployeeLetter[]>(`${V1}/employees/${employeeId}/issued-letters`)).data,
  issueFromTemplate: async (employeeId: number, templateId: number, body: LetterIssuePayload) =>
    (
      await apiClient.post<EmployeeLetter>(
        `${V1}/employees/${employeeId}/issued-letters/from-template/${templateId}`,
        body,
      )
    ).data,
  uploadLetter: async (
    employeeId: number,
    fields: {
      letter_type: LetterType;
      title: string;
      letter_number?: string;
      issued_on?: string;
      visible_to_employee: boolean;
      notes?: string;
    },
    file: File,
  ) =>
    (
      await apiClient.post<EmployeeLetter>(
        `${V1}/employees/${employeeId}/issued-letters/upload`,
        form(fields, file),
        MULTIPART,
      )
    ).data,
  updateLetter: async (
    id: number,
    body: Partial<
      Pick<EmployeeLetter, "letter_type" | "title" | "letter_number" | "issued_on" | "visible_to_employee" | "notes">
    >,
  ) => (await apiClient.patch<EmployeeLetter>(`${V1}/issued-letters/${id}`, body)).data,
  deleteLetter: async (id: number) => {
    await apiClient.delete(`${V1}/issued-letters/${id}`);
  },
  nextLetterNumber: async (letterType: LetterType, onDate?: string) =>
    (
      await apiClient.get<{ letter_number: string }>(`${V1}/issued-letters/next-number`, {
        params: { letter_type: letterType, on_date: onDate || undefined },
      })
    ).data.letter_number,
  letterFileUrl: (id: number) => `${API_BASE_URL}${V1}/issued-letters/${id}/file`,

  // ── Company policies ──────────────────────────────────────────────
  policies: async () =>
    (await apiClient.get<CompanyPolicy[]>(`${V1}/policies`, { params: { include_unpublished: true } }))
      .data,
  createPolicy: async (
    fields: {
      title: string;
      category: PolicyCategory;
      description?: string;
      version?: string;
      effective_date?: string;
      is_published: boolean;
      requires_acknowledgement: boolean;
    },
    file: File,
  ) => (await apiClient.post<CompanyPolicy>(`${V1}/policies`, form(fields, file), MULTIPART)).data,
  updatePolicy: async (
    id: number,
    body: Partial<
      Pick<
        CompanyPolicy,
        | "title"
        | "category"
        | "description"
        | "version"
        | "effective_date"
        | "is_published"
        | "requires_acknowledgement"
      >
    >,
  ) => (await apiClient.patch<CompanyPolicy>(`${V1}/policies/${id}`, body)).data,
  replacePolicyFile: async (id: number, file: File, version?: string, notify = true) =>
    (
      await apiClient.put<CompanyPolicy>(
        `${V1}/policies/${id}/file`,
        form({ version, notify }, file),
        MULTIPART,
      )
    ).data,
  policyAcknowledgements: async (id: number) =>
    (await apiClient.get<PolicyAckReport>(`${V1}/policies/${id}/acknowledgements`)).data,
  remindPolicy: async (id: number) =>
    (await apiClient.post<{ reminded: number }>(`${V1}/policies/${id}/remind`)).data,
  deletePolicy: async (id: number) => {
    await apiClient.delete(`${V1}/policies/${id}`);
  },
  policyFileUrl: (id: number) => `${API_BASE_URL}${V1}/policies/${id}/file`,

  // ── Letterhead ────────────────────────────────────────────────────
  letterhead: async () => (await apiClient.get<Letterhead>(`${V1}/letterhead`)).data,
  updateLetterhead: async (body: LetterheadUpdate) =>
    (await apiClient.put<Letterhead>(`${V1}/letterhead`, body)).data,
  uploadLogo: async (file: File) =>
    (await apiClient.post<Letterhead>(`${V1}/letterhead/logo`, form({}, file), MULTIPART)).data,
  resetLogo: async () => (await apiClient.delete<Letterhead>(`${V1}/letterhead/logo`)).data,
  logoUrl: () => `${API_BASE_URL}${V1}/letterhead/logo`,
  preview: async (draft: LetterheadUpdate) =>
    (await apiClient.post(`${V1}/letterhead/preview`, draft, { responseType: "blob" })).data as Blob,
};

/** Opens a blob (e.g. a generated PDF) in a new tab. */
export function openBlob(blob: Blob) {
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener");
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

export function fmtBytes(n: number | null | undefined) {
  if (!n) return "";
  if (n < 1024 * 1024) return `${Math.max(1, Math.round(n / 1024))} KB`;
  return `${(n / (1024 * 1024)).toFixed(1)} MB`;
}
