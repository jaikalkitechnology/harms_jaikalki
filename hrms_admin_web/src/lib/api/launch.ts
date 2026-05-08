import { apiClient } from "./client";

const v1 = "/api/v1";

export interface NotificationItem {
  id: number;
  channel: string;
  type: string;
  title: string;
  body: string | null;
  data: Record<string, unknown> | null;
  sent_at: string | null;
  read_at: string | null;
  status: string;
  created_at: string;
}

export interface ResignationDocument {
  url: string;
  name: string;
  mime: string | null;
  size: number;
  kind: string;
  uploaded_by: number | null;
  uploaded_at: string;
}

export interface Resignation {
  id: number;
  employee_id: number;
  requested_at: string;
  proposed_last_working_day: string;
  actual_last_working_day: string | null;
  reason: string | null;
  status: string;
  manager_decision_at: string | null;
  manager_decision_by: number | null;
  manager_comment: string | null;
  notice_period_days: number;
  ndc_checklist: Record<string, boolean> | null;
  hr_cleared_at: string | null;
  final_settlement_amount: number | null;
  final_settled_at: string | null;
  exit_interview_notes: string | null;
  documents: ResignationDocument[] | null;
}

export interface AuditLogItem {
  id: number;
  actor_user_id: number | null;
  actor_label: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  request_id: string | null;
  ip: string | null;
  user_agent: string | null;
  method: string | null;
  path: string | null;
  status_code: number | null;
  payload: Record<string, unknown> | null;
  occurred_at: string;
}

export interface BulkImportResult {
  total: number;
  created: number;
  errors: { row: number; error: string }[];
}

export const launchApi = {
  // Notifications
  myNotifications: async (unreadOnly = false) => {
    const { data } = await apiClient.get<NotificationItem[]>(
      `${v1}/notifications/me`,
      { params: { unread_only: unreadOnly } },
    );
    return data;
  },
  unreadCount: async () => {
    const { data } = await apiClient.get<{ unread: number }>(
      `${v1}/notifications/me/unread-count`,
    );
    return data.unread;
  },
  markRead: async (id: number) => {
    const { data } = await apiClient.post<NotificationItem>(
      `${v1}/notifications/${id}/read`,
    );
    return data;
  },
  broadcast: async (payload: {
    audience: "all" | "role" | "department" | "users";
    title: string;
    body?: string | null;
    type?: string;
    send_push?: boolean;
    user_ids?: number[];
    role_codes?: string[];
    department_id?: number;
  }) => {
    const { data } = await apiClient.post<{ queued: number; sent: number }>(
      `${v1}/notifications/broadcast`,
      payload,
    );
    return data;
  },
  markAllRead: async () => {
    const { data } = await apiClient.post<{ marked: number }>(
      `${v1}/notifications/me/read-all`,
    );
    return data.marked;
  },
  // Resignations
  pendingResignations: async () => {
    const { data } = await apiClient.get<Resignation[]>(
      `${v1}/resignations/pending`,
    );
    return data;
  },
  listResignations: async (params?: {
    status?: string;
    employee_id?: number;
    search?: string;
  }) => {
    const { data } = await apiClient.get<Resignation[]>(
      `${v1}/resignations`,
      { params },
    );
    return data;
  },
  uploadResignationDocument: async (
    id: number,
    file: File,
    kind: string,
  ) => {
    const form = new FormData();
    form.append("file", file);
    form.append("kind", kind);
    const { data } = await apiClient.post<Resignation>(
      `${v1}/resignations/${id}/documents`,
      form,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return data;
  },
  removeResignationDocument: async (id: number, docIndex: number) => {
    const { data } = await apiClient.delete<Resignation>(
      `${v1}/resignations/${id}/documents/${docIndex}`,
    );
    return data;
  },
  myResignations: async () => {
    const { data } = await apiClient.get<Resignation[]>(
      `${v1}/resignations/me`,
    );
    return data;
  },
  decideResignation: async (
    id: number,
    accept: boolean,
    comment?: string,
  ) => {
    const { data } = await apiClient.post<Resignation>(
      `${v1}/resignations/${id}/decision`,
      { accept, comment },
    );
    return data;
  },
  updateNdc: async (id: number, updates: Record<string, boolean>) => {
    const { data } = await apiClient.patch<Resignation>(
      `${v1}/resignations/${id}/ndc`,
      { updates },
    );
    return data;
  },
  settleResignation: async (
    id: number,
    amount: number,
    notes?: string,
  ) => {
    const { data } = await apiClient.post<Resignation>(
      `${v1}/resignations/${id}/settle`,
      {
        final_settlement_amount: amount,
        exit_interview_notes: notes,
      },
    );
    return data;
  },
  // Audit
  audit: async (params?: {
    actor_user_id?: number;
    action?: string;
    entity_type?: string;
    entity_id?: string;
    since_days?: number;
    limit?: number;
  }) => {
    const { data } = await apiClient.get<AuditLogItem[]>(`${v1}/audit`, {
      params,
    });
    return data;
  },
  // Bulk import
  bulkImportEmployees: async (file: File) => {
    const form = new FormData();
    form.append("file", file);
    const { data } = await apiClient.post<BulkImportResult>(
      `${v1}/employees/bulk-import`,
      form,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return data;
  },
};
