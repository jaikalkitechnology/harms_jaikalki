import { apiClient } from "./client";

const v1 = "/api/v1";

export interface SalaryRevision {
  id: number;
  employee_id: number;
  proposed_by: number | null;
  reason: string;
  previous_ctc_annual: string;
  new_ctc_annual: string;
  increment_pct: string;
  new_salary_template_id: number | null;
  new_designation_id: number | null;
  effective_date: string;
  notes: string | null;
  breakup_snapshot: Record<string, unknown> | null;
  status: string;
  approved_by: number | null;
  approved_at: string | null;
  applied_at: string | null;
  increment_letter_url: string | null;
  created_at: string;
}

export const compensationApi = {
  pending: async () => {
    const { data } = await apiClient.get<SalaryRevision[]>(
      `${v1}/compensation/revisions/pending`,
    );
    return data;
  },
  listAll: async (params?: {
    employee_id?: number;
    status?: string;
    reason?: string;
    from_date?: string;
    to_date?: string;
  }) => {
    const { data } = await apiClient.get<SalaryRevision[]>(
      `${v1}/compensation/revisions`,
      { params },
    );
    return data;
  },
  update: async (
    id: number,
    payload: {
      new_ctc_annual?: number;
      effective_date?: string;
      reason?: string;
      notes?: string;
    },
  ) => {
    const { data } = await apiClient.put<SalaryRevision>(
      `${v1}/compensation/revisions/${id}`,
      payload,
    );
    return data;
  },
  forEmployee: async (employeeId: number) => {
    const { data } = await apiClient.get<SalaryRevision[]>(
      `${v1}/compensation/revisions/employee/${employeeId}`,
    );
    return data;
  },
  propose: async (payload: {
    employee_id: number;
    new_ctc_annual: number;
    effective_date: string;
    reason: string;
    notes?: string;
    new_salary_template_id?: number | null;
    new_designation_id?: number | null;
  }) => {
    const { data } = await apiClient.post<SalaryRevision>(
      `${v1}/compensation/revisions`,
      payload,
    );
    return data;
  },
  approve: async (id: number) => {
    const { data } = await apiClient.post<SalaryRevision>(
      `${v1}/compensation/revisions/${id}/approve`,
    );
    return data;
  },
  reject: async (id: number, reason?: string) => {
    const { data } = await apiClient.post<SalaryRevision>(
      `${v1}/compensation/revisions/${id}/reject`,
      { reason },
    );
    return data;
  },
  apply: async (id: number) => {
    const { data } = await apiClient.post<SalaryRevision>(
      `${v1}/compensation/revisions/${id}/apply`,
    );
    return data;
  },
  cancel: async (id: number) => {
    const { data } = await apiClient.post<SalaryRevision>(
      `${v1}/compensation/revisions/${id}/cancel`,
    );
    return data;
  },
};
