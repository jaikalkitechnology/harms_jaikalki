import { apiClient } from "./client";

const v1 = "/api/v1";

export interface ApprovalAction {
  id: number;
  level: number;
  approver_id: number;
  action: "approved" | "rejected" | "delegated" | "commented" | "cancelled";
  comments: string | null;
  delegated_to: number | null;
  action_at: string;
}

export interface Approval {
  id: number;
  request_type: string;
  request_id: number;
  employee_id: number | null;
  request_data: Record<string, unknown>;
  title: string;
  summary: string | null;
  current_level: number;
  max_levels: number;
  status: "pending" | "approved" | "rejected" | "cancelled" | "escalated";
  initiated_by: number | null;
  initiated_at: string;
  final_status: string | null;
  final_decision_at: string | null;
  actions: ApprovalAction[];
}

export interface ApprovalCount {
  request_type: string;
  count: number;
}

export const approvalsApi = {
  async inbox(requestType?: string): Promise<Approval[]> {
    const { data } = await apiClient.get(`${v1}/approvals/inbox`, {
      params: requestType ? { request_type: requestType } : undefined,
    });
    return data;
  },
  async counts(): Promise<ApprovalCount[]> {
    const { data } = await apiClient.get(`${v1}/approvals/inbox/counts`);
    return data;
  },
  async history(): Promise<Approval[]> {
    const { data } = await apiClient.get(`${v1}/approvals/history`);
    return data;
  },
  async approve(id: number, comments?: string): Promise<Approval> {
    const { data } = await apiClient.post(`${v1}/approvals/${id}/approve`, {
      comments: comments ?? null,
    });
    return data;
  },
  async reject(id: number, comments?: string): Promise<Approval> {
    const { data } = await apiClient.post(`${v1}/approvals/${id}/reject`, {
      comments: comments ?? null,
    });
    return data;
  },
  async delegate(id: number, toUserId: number, comments?: string): Promise<Approval> {
    const { data } = await apiClient.post(`${v1}/approvals/${id}/delegate`, {
      to_user_id: toUserId,
      comments: comments ?? null,
    });
    return data;
  },
};

export const REQUEST_TYPE_LABEL: Record<string, string> = {
  leave_request: "Leave",
  attendance_regularization: "Regularization",
  intern_expense: "Intern Expense",
};
