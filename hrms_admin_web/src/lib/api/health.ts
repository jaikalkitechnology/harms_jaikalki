import { apiClient } from "./client";

export interface HealthCheck {
  status: string;
  app: string;
  version: string;
  environment: string;
  company: string;
  db: string;
  redis: string;
}

export async function fetchHealth(): Promise<HealthCheck> {
  const { data } = await apiClient.get<HealthCheck>("/health");
  return data;
}

export interface DashboardSummary {
  role: string | null;
  role_level: number;
  user_full_name: string;
  employee_id: number | null;
  employee_code: string | null;
  company_name: string;
  today_attendance: {
    checked_in: boolean;
    checked_out: boolean;
    check_in: string | null;
    check_out: string | null;
    status: string | null;
    work_mode: string | null;
    distance_m: number | null;
  };
  leave_balances: { code: string; name: string; balance: number }[];
  next_payday_in_days: number | null;
  pending_self_leaves: number;
  pending_approvals_count: number;
  pending_by_type: { request_type: string; count: number }[];
  team_size: number;
  team_present_today: number;
  team_attendance_pct: number;
  team_today: { employee_id: number; full_name: string; employee_code: string; status_today: string }[];
  birthdays_today: { employee_id: number; full_name: string; employee_code: string; date_of_birth: string }[];
  probation_expiring_30d: { employee_id: number; full_name: string; employee_code: string; probation_end_date: string; days_remaining: number }[];
  total_headcount: number;
  headcount_by_category: { category: string; count: number }[];
}

export async function fetchDashboardSummary(): Promise<DashboardSummary> {
  const { data } = await apiClient.get<DashboardSummary>(
    "/api/v1/dashboard/me",
  );
  return data;
}
