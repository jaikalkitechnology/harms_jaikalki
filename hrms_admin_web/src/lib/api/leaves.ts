import { apiClient } from "./client";

const v1 = "/api/v1";

export interface LeaveType {
  id: number;
  code: string;
  name: string;
  days_per_year: string;
  carry_forward: boolean;
  encashable: boolean;
  requires_attachment_after_days: number;
  is_active: boolean;
  description: string | null;
}

export interface LeaveBalance {
  id: number;
  employee_id: number;
  leave_type_id: number;
  leave_type: LeaveType | null;
  year: number;
  allocated: string;
  used: string;
  carried_forward: string;
  adjustment: string;
  balance: string;
}

export interface LeaveAdjustment {
  id: number;
  employee_id: number;
  leave_type_id: number;
  year: number;
  delta: string;
  reason: string;
  created_by: number | null;
  created_at: string;
}

export interface LeaveRequest {
  id: number;
  employee_id: number;
  leave_type_id: number;
  leave_type: LeaveType | null;
  from_date: string;
  to_date: string;
  days: string;
  half_day: boolean;
  reason: string | null;
  attachment_url: string | null;
  status: "pending" | "approved" | "rejected" | "cancelled";
  applied_at: string;
  approver_id: number | null;
  approved_at: string | null;
  decision_comment: string | null;
}

export interface Holiday {
  id: number;
  date: string;
  name: string;
  type: "national" | "regional" | "company";
  is_optional: boolean;
  location: string;
}

export interface CalendarItem {
  employee_id: number;
  employee_code: string;
  full_name: string;
  from_date: string;
  to_date: string;
  leave_type: string;
  days: string;
  status: string;
}

export const leavesApi = {
  async types(): Promise<LeaveType[]> {
    const { data } = await apiClient.get(`${v1}/leaves/types`);
    return data;
  },
  async myBalance(year?: number): Promise<LeaveBalance[]> {
    const { data } = await apiClient.get(`${v1}/leaves/balance`, {
      params: year ? { year } : undefined,
    });
    return data;
  },
  async employeeBalance(employeeId: number, year?: number): Promise<LeaveBalance[]> {
    const { data } = await apiClient.get(
      `${v1}/leaves/balance/${employeeId}`,
      { params: year ? { year } : undefined },
    );
    return data;
  },
  async adjustBalance(
    employeeId: number,
    payload: {
      leave_type_id: number;
      delta: number;
      reason: string;
      year?: number;
    },
  ): Promise<LeaveBalance> {
    const { data } = await apiClient.post(
      `${v1}/leaves/balance/${employeeId}/adjust`,
      payload,
    );
    return data;
  },
  async listAdjustments(
    employeeId: number,
    year?: number,
  ): Promise<LeaveAdjustment[]> {
    const { data } = await apiClient.get(
      `${v1}/leaves/balance/${employeeId}/adjustments`,
      { params: year ? { year } : undefined },
    );
    return data;
  },
  async myRequests(status?: string): Promise<LeaveRequest[]> {
    const { data } = await apiClient.get(`${v1}/leaves/requests`, {
      params: status ? { status } : undefined,
    });
    return data;
  },
  async pending(): Promise<LeaveRequest[]> {
    const { data } = await apiClient.get(`${v1}/leaves/pending-approvals`);
    return data;
  },
  async apply(payload: {
    leave_type_id: number;
    from_date: string;
    to_date: string;
    reason?: string;
    half_day?: boolean;
    attachment_url?: string;
  }): Promise<LeaveRequest> {
    const { data } = await apiClient.post(`${v1}/leaves/apply`, payload);
    return data;
  },
  async cancel(id: number): Promise<LeaveRequest> {
    const { data } = await apiClient.delete(`${v1}/leaves/requests/${id}`);
    return data;
  },
  async approve(id: number, comment?: string): Promise<LeaveRequest> {
    const { data } = await apiClient.post(`${v1}/leaves/${id}/approve`, {
      decision_comment: comment ?? null,
    });
    return data;
  },
  async reject(id: number, comment?: string): Promise<LeaveRequest> {
    const { data } = await apiClient.post(`${v1}/leaves/${id}/reject`, {
      decision_comment: comment ?? null,
    });
    return data;
  },
  async calendar(from: string, to: string): Promise<CalendarItem[]> {
    const { data } = await apiClient.get(`${v1}/leaves/calendar`, {
      params: { from, to },
    });
    return data;
  },
  async holidays(year?: number): Promise<Holiday[]> {
    const { data } = await apiClient.get(`${v1}/leaves/holidays`, {
      params: year ? { year } : undefined,
    });
    return data;
  },
  async createHoliday(payload: {
    date: string;
    name: string;
    type?: string;
    is_optional?: boolean;
    location?: string;
  }): Promise<Holiday> {
    const { data } = await apiClient.post(`${v1}/leaves/holidays`, payload);
    return data;
  },
  async deleteHoliday(id: number): Promise<void> {
    await apiClient.delete(`${v1}/leaves/holidays/${id}`);
  },
};
