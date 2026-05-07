import { apiClient } from "./client";

const v1 = "/api/v1";

export interface DwpField {
  field_key: string;
  value: string | null;
  file_url: string | null;
}

export interface DwpComment {
  id: number;
  submission_id: number;
  commented_by: number;
  comment: string;
  is_kudos: boolean;
  created_at: string;
}

export interface DwpSubmission {
  id: number;
  employee_id: number;
  template_id: number;
  type: "morning" | "eod";
  date: string;
  submitted_at: string;
  total_hours: string | null;
  mood_rating: number | null;
  linked_morning_id: number | null;
  fields: DwpField[];
  comments: DwpComment[];
}

export interface DwpTeamItem {
  submission: DwpSubmission;
  employee_code: string;
  employee_full_name: string;
}

export interface DwpTemplateField {
  key: string;
  label: string;
  field_type: string;
  is_required: boolean;
  options: string[] | null;
  placeholder: string | null;
  sort_order: number;
}

export interface DwpTemplateLite {
  id: number;
  type: "morning" | "eod";
  department_id: number | null;
  fields: DwpTemplateField[];
}

export interface AdminDwpListResponse {
  items: DwpSubmission[];
  total: number;
  page: number;
  per_page: number;
}

export const dwpApi = {
  async teamToday(date?: string): Promise<DwpTeamItem[]> {
    const { data } = await apiClient.get(`${v1}/dwp/team/today`, {
      params: date ? { date } : undefined,
    });
    return data;
  },
  async teamBlockers(date?: string): Promise<DwpTeamItem[]> {
    const { data } = await apiClient.get(`${v1}/dwp/team/blockers`, {
      params: date ? { date } : undefined,
    });
    return data;
  },
  async addComment(
    submissionId: number,
    comment: string,
    isKudos: boolean,
  ): Promise<DwpComment> {
    const { data } = await apiClient.post(
      `${v1}/dwp/${submissionId}/comment`,
      { comment, is_kudos: isKudos },
    );
    return data;
  },

  // Admin
  async adminTemplates(): Promise<DwpTemplateLite[]> {
    const { data } = await apiClient.get(`${v1}/dwp/admin/templates`);
    return data;
  },
  async adminList(params: {
    employee_id?: number;
    type?: "morning" | "eod";
    from_date?: string;
    to_date?: string;
    page?: number;
    per_page?: number;
  }): Promise<AdminDwpListResponse> {
    const { data } = await apiClient.get(`${v1}/dwp/admin/submissions`, {
      params,
    });
    return data;
  },
  async adminSubmit(body: {
    employee_id: number;
    template_id: number;
    fields: Record<string, unknown>;
    total_hours?: number;
    mood_rating?: number;
    on_date?: string;
  }): Promise<DwpSubmission> {
    const { data } = await apiClient.post(`${v1}/dwp/admin/submit`, body);
    return data;
  },
  async adminUpdate(
    id: number,
    body: {
      fields?: Record<string, unknown>;
      total_hours?: number;
      mood_rating?: number;
    },
  ): Promise<DwpSubmission> {
    const { data } = await apiClient.put(
      `${v1}/dwp/admin/submissions/${id}`,
      body,
    );
    return data;
  },
  async adminDelete(id: number): Promise<void> {
    await apiClient.delete(`${v1}/dwp/admin/submissions/${id}`);
  },
};
