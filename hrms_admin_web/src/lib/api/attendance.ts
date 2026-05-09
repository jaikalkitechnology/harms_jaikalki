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
