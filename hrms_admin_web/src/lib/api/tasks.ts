// Tasks managers give to people in their team.
import { apiClient } from "./client";

const V1 = "/api/v1";

export type TaskPriority = "low" | "medium" | "high" | "urgent";
export type TaskStatus = "open" | "in_progress" | "done" | "cancelled";

export interface WorkTask {
  id: number;
  title: string;
  description: string | null;
  assigned_to: number;
  assignee_name: string;
  assignee_code: string | null;
  assigned_by: number | null;
  assigner_name: string | null;
  due_date: string | null;
  priority: TaskPriority;
  status: TaskStatus;
  is_overdue: boolean;
  completed_at: string | null;
  completion_note: string | null;
  escalation_level: number;
  comment_count: number;
  created_at: string | null;
  updated_at: string | null;
  can_manage: boolean;
  is_mine: boolean;
}

export interface TaskComment {
  id: number;
  task_id: number;
  user_id: number | null;
  author_name: string;
  body: string;
  created_at: string | null;
}

export type TaskView = "team" | "given" | "mine";
export type TaskFilter = "open" | "overdue" | "done" | "all";

export const PRIORITY: Record<TaskPriority, { label: string; tone: "neutral" | "info" | "warning" | "error" }> = {
  low: { label: "Low", tone: "neutral" },
  medium: { label: "Medium", tone: "info" },
  high: { label: "High", tone: "warning" },
  urgent: { label: "Urgent", tone: "error" },
};

export const STATUS: Record<TaskStatus, { label: string; tone: "neutral" | "info" | "success" | "warning" }> = {
  open: { label: "To do", tone: "neutral" },
  in_progress: { label: "In progress", tone: "info" },
  done: { label: "Done", tone: "success" },
  cancelled: { label: "Cancelled", tone: "neutral" },
};

export const tasksApi = {
  list: async (params: { view: TaskView; status: TaskFilter; employee_id?: number; scope?: "direct" | "all" }) =>
    (await apiClient.get<WorkTask[]>(`${V1}/tasks`, { params })).data,
  get: async (id: number) => (await apiClient.get<WorkTask>(`${V1}/tasks/${id}`)).data,
  create: async (body: {
    title: string;
    description?: string;
    assigned_to: number;
    due_date?: string;
    priority: TaskPriority;
  }) => (await apiClient.post<WorkTask>(`${V1}/tasks`, body)).data,
  update: async (
    id: number,
    body: Partial<{
      title: string;
      description: string | null;
      assigned_to: number;
      due_date: string | null;
      priority: TaskPriority;
      status: TaskStatus;
      completion_note: string | null;
    }>,
  ) => (await apiClient.patch<WorkTask>(`${V1}/tasks/${id}`, body)).data,
  remove: async (id: number) => {
    await apiClient.delete(`${V1}/tasks/${id}`);
  },
  comments: async (id: number) => (await apiClient.get<TaskComment[]>(`${V1}/tasks/${id}/comments`)).data,
  addComment: async (id: number, body: string) =>
    (await apiClient.post<TaskComment>(`${V1}/tasks/${id}/comments`, { body })).data,
};
