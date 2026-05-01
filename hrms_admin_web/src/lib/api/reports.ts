import { apiClient } from "./client";

const v1 = "/api/v1";

export interface HeadcountPoint {
  period: string;
  headcount: number;
  joined: number;
  exited: number;
}

export interface HeadcountTrend {
  months: number;
  points: HeadcountPoint[];
  current_headcount: number;
}

export interface AttritionStats {
  period_months: number;
  starting_headcount: number;
  exits: number;
  attrition_pct: number;
}

export interface DepartmentBreakdown {
  department: string;
  headcount: number;
}

export interface ComplianceStats {
  mandatory_courses: number;
  employees_total: number;
  fully_compliant: number;
  partially_compliant: number;
  non_compliant: number;
  coverage_pct: number;
}

export interface VerificationStats {
  total: number;
  completed: number;
  in_progress: number;
  audit_pending: number;
  breach_pct: number;
  avg_hours: number;
}

export interface TrainingStats {
  sessions_total: number;
  sessions_completed: number;
  upcoming_sessions: number;
  total_attendees: number;
}

export interface SalesStats {
  period_start: string;
  period_end: string;
  leads_count: number;
  leads_won: number;
  win_rate_pct: number;
  quotes_total: string;
  orders_total: string;
}

export interface PayrollCostStats {
  year: number;
  month: number;
  total_gross: string;
  total_net: string;
  total_employer_cost: string;
  employee_count: number;
  avg_cost_per_employee: string;
}

export interface DirectorDashboard {
  headcount: HeadcountTrend;
  attrition: AttritionStats;
  department_breakdown: DepartmentBreakdown[];
  payroll_this_month: PayrollCostStats | null;
  compliance: ComplianceStats;
  sales: SalesStats | null;
  verification: VerificationStats;
  training: TrainingStats;
}

export interface SavedReport {
  id: number;
  code: string;
  name: string;
  description: string | null;
  report_type: string;
  filters: Record<string, unknown> | null;
  schedule_cron: string | null;
  schedule_recipients: string[] | null;
  last_run_at: string | null;
  is_shared: boolean;
  created_by: number | null;
}

export const reportsApi = {
  directorDashboard: async () => {
    const { data } = await apiClient.get<DirectorDashboard>(
      `${v1}/reports/director-dashboard`,
    );
    return data;
  },
  headcount: async (months = 12) => {
    const { data } = await apiClient.get<HeadcountTrend>(
      `${v1}/reports/headcount`,
      { params: { months } },
    );
    return data;
  },
  attrition: async (months = 12) => {
    const { data } = await apiClient.get<AttritionStats>(
      `${v1}/reports/attrition`,
      { params: { months } },
    );
    return data;
  },
  departmentBreakdown: async () => {
    const { data } = await apiClient.get<DepartmentBreakdown[]>(
      `${v1}/reports/department-breakdown`,
    );
    return data;
  },
  compliance: async () => {
    const { data } = await apiClient.get<ComplianceStats>(
      `${v1}/reports/compliance`,
    );
    return data;
  },
  listSaved: async () => {
    const { data } = await apiClient.get<SavedReport[]>(
      `${v1}/reports/saved`,
    );
    return data;
  },
  createSaved: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<SavedReport>(
      `${v1}/reports/saved`,
      payload,
    );
    return data;
  },
  deleteSaved: async (id: number) => {
    await apiClient.delete(`${v1}/reports/saved/${id}`);
  },
};
