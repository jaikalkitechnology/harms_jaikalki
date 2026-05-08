import { apiClient } from "./client";
import { API_BASE_URL } from "@/lib/constants";

const v1 = "/api/v1";

export interface TemplateField {
  key: string;
  label: string;
  field_type: string;
  required: boolean;
  options?: string[] | null;
  help_text?: string | null;
}

export interface PhotoRequirement {
  key: string;
  label: string;
  required: boolean;
}

export interface VerificationTemplate {
  id: number;
  code: string;
  name: string;
  type: string;
  description: string | null;
  fields: TemplateField[];
  photo_requirements: PhotoRequirement[] | null;
  signature_required: boolean;
  sla_hours: number;
  is_active: boolean;
}

export interface FraudFlag {
  id: number;
  verification_id: number;
  flag_type: string;
  severity: string;
  detected_by: string;
  notes: string | null;
  detected_at: string;
}

export interface Verification {
  id: number;
  ticket_number: string;
  template_id: number;
  type: string;
  subject_name: string;
  subject_data: Record<string, unknown>;
  address: string | null;
  contact_phone: string | null;
  requested_by_org: string | null;
  assigned_to: number | null;
  assigned_at: string;
  deadline_at: string | null;
  status: string;
  form_data: Record<string, unknown> | null;
  photos: string[] | null;
  signature_url: string | null;
  geo_lat: string | null;
  geo_lng: string | null;
  submitted_at: string | null;
  result: string | null;
  remarks: string | null;
  audited_by: number | null;
  audited_at: string | null;
  audit_status: string | null;
  audit_comments: string | null;
  fraud_flags: FraudFlag[];
}

export interface TatStat {
  total: number;
  on_time: number;
  breached: number;
  avg_hours: number;
  breach_pct: number;
}

export const verificationApi = {
  templates: async (params?: {
    search?: string;
    type?: string;
    include_inactive?: boolean;
  }) => {
    const { data } = await apiClient.get<VerificationTemplate[]>(
      `${v1}/verification/templates`,
      { params },
    );
    return data;
  },
  createTemplate: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<VerificationTemplate>(
      `${v1}/verification/templates`,
      payload,
    );
    return data;
  },
  updateTemplate: async (id: number, payload: Record<string, unknown>) => {
    const { data } = await apiClient.put<VerificationTemplate>(
      `${v1}/verification/templates/${id}`,
      payload,
    );
    return data;
  },
  deleteTemplate: async (id: number) => {
    await apiClient.delete(`${v1}/verification/templates/${id}`);
  },
  list: async (params?: {
    mine?: boolean;
    status?: string;
    type?: string;
    search?: string;
    fraud_only?: boolean;
    assigned_to?: number;
  }) => {
    const { data } = await apiClient.get<Verification[]>(
      `${v1}/verification/`,
      { params },
    );
    return data;
  },
  create: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<Verification>(
      `${v1}/verification/`,
      payload,
    );
    return data;
  },
  update: async (id: number, payload: Record<string, unknown>) => {
    const { data } = await apiClient.put<Verification>(
      `${v1}/verification/${id}`,
      payload,
    );
    return data;
  },
  auditQueue: async (params?: {
    search?: string;
    type?: string;
    fraud_only?: boolean;
  }) => {
    const { data } = await apiClient.get<Verification[]>(
      `${v1}/verification/audit-queue`,
      { params },
    );
    return data;
  },
  audit: async (
    id: number,
    auditStatus: "approved" | "rejected" | "rework",
    comments?: string,
  ) => {
    const { data } = await apiClient.post<Verification>(
      `${v1}/verification/${id}/audit`,
      { audit_status: auditStatus, audit_comments: comments },
    );
    return data;
  },
  tatStats: async () => {
    const { data } = await apiClient.get<TatStat>(
      `${v1}/verification/tat-stats`,
    );
    return data;
  },
  reportUrl: (id: number) => `${API_BASE_URL}${v1}/verification/${id}/report`,
};
