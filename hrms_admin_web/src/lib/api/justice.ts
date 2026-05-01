import { apiClient } from "./client";

const v1 = "/api/v1";

export interface ComplaintListItem {
  id: number;
  ticket_number: string;
  complaint_type: string;
  privacy_level: "anonymous" | "confidential" | "open";
  severity: "low" | "medium" | "high" | "critical";
  status: string;
  subject: string;
  submitted_at: string;
  deadline_at: string | null;
  is_anonymous: boolean;
}

export interface ComplaintDetail extends ComplaintListItem {
  description: string | null;
  desired_outcome: string | null;
  incident_date: string | null;
  incident_location: string | null;
  acknowledged_at: string | null;
  resolved_at: string | null;
  assigned_to: number | null;
  complainant_employee_id: number | null;
  accused: Array<{
    id: number;
    name: string | null;
    accused_employee_id: number | null;
    relationship_type: string | null;
  }>;
  witnesses: Array<{
    id: number;
    name: string | null;
    statement: string | null;
    is_anonymous: boolean;
  }>;
  evidence: Array<{
    id: number;
    file_url: string | null;
    file_name: string | null;
    file_type: string | null;
    file_hash: string | null;
  }>;
  actions: Array<{
    id: number;
    action_type: string;
    action_date: string;
    taken_by: number | null;
    notes: string | null;
  }>;
  timeline: Array<{
    id: number;
    event_type: string;
    event_description: string | null;
    event_date: string;
    done_by: number | null;
  }>;
  access_log: Array<{
    id: number;
    user_id: number | null;
    action: string;
    timestamp: string;
    ip_address: string | null;
  }>;
}

export interface IccMember {
  id: number;
  member_name: string;
  user_id: number | null;
  role: "presiding_officer" | "member" | "external_member" | "secretary";
  gender: string | null;
  is_external: boolean;
  term_start: string;
  term_end: string | null;
  is_active: boolean;
  contact: string | null;
}

export interface IccComplianceStatus {
  compliant: boolean;
  reasons: string[];
  member_count: number;
  women_count: number;
  external_count: number;
  has_presiding_officer: boolean;
}

export interface PoshAnnualReport {
  id: number;
  year: number;
  total_complaints: number;
  resolved: number;
  pending: number;
  actions_taken_json: Record<string, number> | null;
  generated_at: string;
}

export const justiceApi = {
  async inbox(): Promise<ComplaintListItem[]> {
    const { data } = await apiClient.get(`${v1}/justice/inbox`);
    return data;
  },
  async detail(id: number): Promise<ComplaintDetail> {
    const { data } = await apiClient.get(`${v1}/justice/${id}`);
    return data;
  },
  async assign(id: number, userId: number): Promise<ComplaintListItem> {
    const { data } = await apiClient.post(`${v1}/justice/${id}/assign`, {
      user_id: userId,
    });
    return data;
  },
  async addAction(
    id: number,
    actionType: string,
    notes?: string,
  ): Promise<unknown> {
    const { data } = await apiClient.post(`${v1}/justice/${id}/action`, {
      action_type: actionType,
      notes: notes ?? null,
    });
    return data;
  },
  async resolve(id: number, notes?: string): Promise<ComplaintListItem> {
    const { data } = await apiClient.post(`${v1}/justice/${id}/resolve`, {
      notes: notes ?? null,
      action_type: "case_closed",
    });
    return data;
  },

  async iccMembers(): Promise<IccMember[]> {
    const { data } = await apiClient.get(`${v1}/justice/icc/members`);
    return data;
  },
  async iccCompliance(): Promise<IccComplianceStatus> {
    const { data } = await apiClient.get(`${v1}/justice/icc/compliance`);
    return data;
  },
  async addIccMember(payload: {
    member_name: string;
    role: string;
    gender?: string;
    is_external?: boolean;
    term_start: string;
    term_end?: string;
    contact?: string;
  }): Promise<IccMember> {
    const { data } = await apiClient.post(`${v1}/justice/icc/members`, payload);
    return data;
  },
  async deactivateIccMember(id: number): Promise<void> {
    await apiClient.delete(`${v1}/justice/icc/members/${id}`);
  },
  async poshAnnualReport(year: number): Promise<PoshAnnualReport> {
    const { data } = await apiClient.get(
      `${v1}/justice/posh/annual-report?year=${year}`,
    );
    return data;
  },
};

export const COMPLAINT_TYPE_LABEL: Record<string, string> = {
  sexual_harassment: "Sexual Harassment (POSH)",
  fraud: "Fraud",
  manager_issue: "Manager issue",
  hr_issue: "HR issue",
  director_issue: "Director issue",
  safety: "Safety",
  discrimination: "Discrimination (POSH)",
  general: "General grievance",
};

export const SEVERITY_LABEL: Record<string, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  critical: "Critical",
};
