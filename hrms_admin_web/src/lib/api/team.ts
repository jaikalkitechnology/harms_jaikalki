// My Team: everyone below the signed-in manager, level by level (the
// whole company for Director / HR / Admin).
import { apiClient } from "./client";
import type { AttendanceCalendar } from "./attendance";
import type { DwpSubmission } from "./dwp";

const V1 = "/api/v1";

export type DayStatus =
  | "present"
  | "late"
  | "wfh"
  | "half_day"
  | "on_leave"
  | "absent"
  | "not_in"
  | "off";

export interface TeamTarget {
  period_type: string;
  period_start: string;
  period_end: string;
  target_amount: string;
  achieved_amount: string;
  achievement_pct: number | null;
}

export interface TeamRollup {
  size: number;
  present: number;
  late: number;
  wfh: number;
  half_day: number;
  on_leave: number;
  absent: number;
  not_in: number;
  off: number;
  present_total: number;
  attendance_pct: number | null;
  dwp_morning: number;
  dwp_eod: number;
  with_target: number;
  target_amount: string;
  achieved_amount: string;
  target_pct: number | null;
}

export interface TeamToday {
  status: DayStatus;
  check_in: string | null;
  check_out: string | null;
}

export interface TeamMemberRow {
  employee_id: number;
  employee_code: string;
  name: string;
  designation: string | null;
  department: string | null;
  photo_url: string | null;
  reporting_to: number | null;
  manager_name: string | null;
  level: number;
  direct_reports: number;
  today: TeamToday;
  dwp_morning: boolean;
  dwp_eod: boolean;
  target: TeamTarget | null;
  team: TeamRollup | null;
}

export interface TeamOverview {
  root: { employee_id: number; name: string; designation: string | null; reporting_to: number | null } | null;
  scope: "direct" | "all";
  on_date: string;
  summary: TeamRollup;
  direct_count: number;
  members: TeamMemberRow[];
}

export interface TeamMemberDetail {
  employee_id: number;
  employee_code: string;
  name: string;
  designation: string | null;
  department: string | null;
  photo_url: string | null;
  status: string;
  date_of_joining: string | null;
  work_mode: string;
  work_location: string;
  phone: string | null;
  email: string | null;
  chain: { employee_id: number; name: string; designation: string | null }[];
  is_direct_report: boolean;
  on_date: string;
  today: TeamToday;
  dwp_morning: boolean;
  dwp_eod: boolean;
  target: TeamTarget | null;
  direct_reports: number;
  team: TeamRollup | null;
  recent_leaves: {
    id: number;
    leave_type: string;
    from_date: string;
    to_date: string;
    days: string;
    status: string;
    reason: string | null;
  }[];
}

export interface OrgNode {
  employee_id: number;
  employee_code: string;
  name: string;
  designation: string | null;
  department: string | null;
  photo_url: string | null;
  status_today: DayStatus;
  team_size: number;
  children: OrgNode[];
}

export interface TeamInfo {
  employee_id: number | null;
  has_team: boolean;
  sees_everyone: boolean;
  direct_count: number;
  team_size: number | null;
}

export const teamApi = {
  me: async () => (await apiClient.get<TeamInfo>(`${V1}/team/me`)).data,
  overview: async (params: { scope: "direct" | "all"; root_id?: number; date?: string }) =>
    (await apiClient.get<TeamOverview>(`${V1}/team/overview`, { params })).data,
  member: async (id: number, date?: string) =>
    (await apiClient.get<TeamMemberDetail>(`${V1}/team/members/${id}`, { params: { date } })).data,
  orgChart: async (date?: string) =>
    (await apiClient.get<OrgNode[]>(`${V1}/team/org-chart`, { params: { date } })).data,
  calendar: async (id: number, year: number, month: number) =>
    (
      await apiClient.get<AttendanceCalendar>(`${V1}/attendance/employee/${id}/calendar`, {
        params: { year, month },
      })
    ).data,
  dailyPlans: async (id: number) =>
    (await apiClient.get<DwpSubmission[]>(`${V1}/dwp/employee/${id}/history`, { params: { limit: 14 } }))
      .data,
};

export const DAY_STATUS: Record<DayStatus, { label: string; tone: "success" | "warning" | "error" | "info" | "neutral" | "gold" }> = {
  present: { label: "Present", tone: "success" },
  late: { label: "Late", tone: "warning" },
  wfh: { label: "WFH", tone: "info" },
  half_day: { label: "Half day", tone: "gold" },
  on_leave: { label: "On leave", tone: "info" },
  absent: { label: "Absent", tone: "error" },
  not_in: { label: "Not in yet", tone: "neutral" },
  off: { label: "Off", tone: "neutral" },
};
