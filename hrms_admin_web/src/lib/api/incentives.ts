// Incentive schemes, monthly runs, manager review and HR approval.
import { apiClient } from "./client";
import type { TargetMetric } from "./sales";

const V1 = "/api/v1/incentives";

export interface Slab {
  min_pct: number;
  value: number;
}

export interface IncentiveScheme {
  id: number;
  name: string;
  description: string | null;
  metric: TargetMetric;
  period_type: "monthly" | "quarterly";
  payout_type: "fixed" | "percent_of_achieved";
  slabs: Slab[];
  max_payout: string | null;
  department_ids: number[] | null;
  category_codes: string[] | null;
  designation_ids: number[] | null;
  min_attendance_pct: number | null;
  confirmed_only: boolean;
  exclude_notice: boolean;
  no_warning_days: number | null;
  min_tenure_days: number | null;
  is_active: boolean;
  created_at: string | null;
}
export type SchemeInput = Omit<IncentiveScheme, "id" | "created_at" | "max_payout"> & {
  max_payout: number | null;
};

export interface IncentiveRunSummary {
  id: number;
  scheme_id: number;
  scheme_name: string;
  metric: TargetMetric;
  period_start: string;
  period_end: string;
  period_label: string;
  payout_year: number;
  payout_month: number;
  status: "review" | "approved" | "cancelled";
  lines: number;
  eligible: number;
  pending_review: number;
  paid_lines: number;
  total_amount: string;
  approved_at: string | null;
}

export interface IncentiveLine {
  id: number;
  run_id: number;
  scheme_name: string | null;
  metric: TargetMetric | null;
  period_label: string | null;
  run_status: string | null;
  employee_id: number;
  employee_name: string;
  employee_code: string | null;
  designation: string | null;
  manager_name: string | null;
  target_amount: string;
  achieved_amount: string;
  achievement_pct: number;
  slab_min_pct: number | null;
  attendance_pct: number | null;
  eligible: boolean;
  reasons: string[];
  calculated_amount: string;
  amount: string | null;
  review_status: "pending" | "approved" | "adjusted" | "rejected";
  review_note: string | null;
  reviewed_at: string | null;
  paid: boolean;
  in_payroll: boolean;
  payout_label: string | null;
}

export type IncentiveRunDetail = IncentiveRunSummary & { lines_detail: IncentiveLine[] };

export const incentivesApi = {
  schemes: async () => (await apiClient.get<IncentiveScheme[]>(`${V1}/schemes`)).data,
  createScheme: async (b: SchemeInput) => (await apiClient.post<IncentiveScheme>(`${V1}/schemes`, b)).data,
  updateScheme: async (id: number, b: Partial<SchemeInput>) =>
    (await apiClient.put<IncentiveScheme>(`${V1}/schemes/${id}`, b)).data,
  deleteScheme: async (id: number) => {
    await apiClient.delete(`${V1}/schemes/${id}`);
  },
  runs: async () => (await apiClient.get<IncentiveRunSummary[]>(`${V1}/runs`)).data,
  calculate: async (b: { scheme_id: number; period_date: string; payout_year?: number; payout_month?: number }) =>
    (await apiClient.post<IncentiveRunSummary>(`${V1}/runs`, b)).data,
  run: async (id: number) => (await apiClient.get<IncentiveRunDetail>(`${V1}/runs/${id}`)).data,
  updateRun: async (id: number, b: { payout_year: number; payout_month: number }) =>
    (await apiClient.patch<IncentiveRunSummary>(`${V1}/runs/${id}`, b)).data,
  recalculate: async (id: number) => (await apiClient.post<IncentiveRunSummary>(`${V1}/runs/${id}/recalculate`)).data,
  approve: async (id: number, approve_pending: boolean) =>
    (await apiClient.post<IncentiveRunSummary>(`${V1}/runs/${id}/approve`, { approve_pending })).data,
  reopen: async (id: number) => (await apiClient.post<IncentiveRunSummary>(`${V1}/runs/${id}/reopen`)).data,
  cancel: async (id: number) => (await apiClient.post<IncentiveRunSummary>(`${V1}/runs/${id}/cancel`)).data,
  reviewQueue: async () => (await apiClient.get<IncentiveLine[]>(`${V1}/review`)).data,
  review: async (lineId: number, b: { action: "approve" | "adjust" | "reject" | "reset"; amount?: number; note?: string }) =>
    (await apiClient.post<IncentiveLine>(`${V1}/lines/${lineId}/review`, b)).data,
};

export const REVIEW_STATUS: Record<IncentiveLine["review_status"], { label: string; tone: "neutral" | "success" | "info" | "error" }> = {
  pending: { label: "To review", tone: "neutral" },
  approved: { label: "Approved", tone: "success" },
  adjusted: { label: "Adjusted", tone: "info" },
  rejected: { label: "Rejected", tone: "error" },
};
