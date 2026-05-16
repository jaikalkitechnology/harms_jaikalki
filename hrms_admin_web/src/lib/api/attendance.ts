import { apiClient } from "./client";

const v1 = "/api/v1";

export interface AttendanceRecord {
  id: number;
  employee_id: number;
  date: string;
  check_in: string | null;
  check_in_lat: string | null;
  check_in_lng: string | null;
  check_in_selfie_url: string | null;
  check_in_distance_m: number | null;
  check_out: string | null;
  status: "present" | "absent" | "half_day" | "wfh" | "leave" | "holiday";
  work_mode: string;
  source: string;
  total_minutes: number;
  notes: string | null;
}

export interface CalendarDay {
  date: string;
  weekday: number;
  status: string;
  is_sunday: boolean;
  is_holiday: boolean;
  holiday_name: string | null;
  is_editable: boolean;
  attendance_id: number | null;
  check_in: string | null;
  check_out: string | null;
  work_mode: string | null;
  total_minutes: number;
  notes: string | null;
  leave_type: string | null;
  is_late: boolean;
  late_remark: string | null;
}

export interface AttendanceCalendar {
  year: number;
  month: number;
  employee_id: number;
  days: CalendarDay[];
  days_present: number;
  days_absent: number;
  days_leave: number;
  days_holiday: number;
  days_weekoff: number;
  days_half_day: number;
  days_wfh: number;
  working_days: number;
}

export interface YearMonthSummary {
  month: number;
  days_present: number;
  days_absent: number;
  days_leave: number;
  days_holiday: number;
  days_weekoff: number;
  days_half_day: number;
  days_wfh: number;
  working_days: number;
}

export interface AttendanceYearSummary {
  employee_id: number;
  year: number;
  months: YearMonthSummary[];
  total_present: number;
  total_absent: number;
  total_leave: number;
  total_holiday: number;
  total_weekoff: number;
  total_half_day: number;
  total_wfh: number;
  total_working_days: number;
}

export interface AttendanceUpsertByDate {
  date: string;
  status?: AttendanceRecord["status"] | null;
  check_in?: string | null;
  check_out?: string | null;
  work_mode?: string | null;
  notes?: string | null;
  is_late?: boolean | null;
  late_remark?: string | null;
}

export interface AttendanceUploadRowError {
  row: number;
  employee_code: string | null;
  date: string | null;
  error: string;
}

export interface AttendanceUploadResult {
  rows_total: number;
  rows_imported: number;
  rows_updated: number;
  rows_skipped: number;
  errors: AttendanceUploadRowError[];
}

export interface RegularizationRequest {
  id: number;
  employee_id: number;
  date: string;
  requested_check_in: string | null;
  requested_check_out: string | null;
  reason: string;
  status: "pending" | "approved" | "rejected";
  approver_id: number | null;
  approved_at: string | null;
  decision_comment: string | null;
  created_at: string;
}

export const attendanceApi = {
  async team(date?: string): Promise<AttendanceRecord[]> {
    const { data } = await apiClient.get(`${v1}/attendance/team`, {
      params: date ? { date } : undefined,
    });
    return data;
  },
  async report(params: {
    from_date: string;
    to_date: string;
    employee_id?: number;
  }): Promise<AttendanceRecord[]> {
    const { data } = await apiClient.get(`${v1}/attendance/report`, { params });
    return data;
  },
  async update(
    id: number,
    body: Partial<{
      status: AttendanceRecord["status"];
      check_in: string | null;
      check_out: string | null;
      work_mode: string;
      notes: string | null;
    }>,
  ): Promise<AttendanceRecord> {
    const { data } = await apiClient.put(`${v1}/attendance/${id}`, body);
    return data;
  },
  exportCsvUrl(params: {
    from_date: string;
    to_date: string;
    employee_id?: number;
  }): string {
    const q = new URLSearchParams({
      from_date: params.from_date,
      to_date: params.to_date,
    });
    if (params.employee_id) q.set("employee_id", String(params.employee_id));
    return `${v1}/attendance/report.csv?${q.toString()}`;
  },
  async employeeCalendar(
    employeeId: number,
    year: number,
    month: number,
  ): Promise<AttendanceCalendar> {
    const { data } = await apiClient.get(
      `${v1}/attendance/employee/${employeeId}/calendar`,
      { params: { year, month } },
    );
    return data;
  },
  async employeeYearSummary(
    employeeId: number,
    year: number,
  ): Promise<AttendanceYearSummary> {
    const { data } = await apiClient.get(
      `${v1}/attendance/employee/${employeeId}/year-summary`,
      { params: { year } },
    );
    return data;
  },
  async upsertByDate(
    employeeId: number,
    body: AttendanceUpsertByDate,
  ): Promise<AttendanceRecord> {
    const { data } = await apiClient.put(
      `${v1}/attendance/employee/${employeeId}/by-date`,
      body,
    );
    return data;
  },
  async upload(file: File): Promise<AttendanceUploadResult> {
    const fd = new FormData();
    fd.append("file", file);
    const { data } = await apiClient.post(`${v1}/attendance/upload`, fd, {
      headers: { "Content-Type": "multipart/form-data" },
    });
    return data;
  },
  uploadTemplateUrl(): string {
    return `${v1}/attendance/upload/template.csv`;
  },
  async pendingRegularizations(): Promise<RegularizationRequest[]> {
    const { data } = await apiClient.get(`${v1}/attendance/regularize/pending`);
    return data;
  },
  async approveRegularization(
    id: number,
    comment?: string,
  ): Promise<RegularizationRequest> {
    const { data } = await apiClient.post(
      `${v1}/attendance/regularize/${id}/approve`,
      { decision_comment: comment ?? null },
    );
    return data;
  },
  async rejectRegularization(
    id: number,
    comment?: string,
  ): Promise<RegularizationRequest> {
    const { data } = await apiClient.post(
      `${v1}/attendance/regularize/${id}/reject`,
      { decision_comment: comment ?? null },
    );
    return data;
  },
};
