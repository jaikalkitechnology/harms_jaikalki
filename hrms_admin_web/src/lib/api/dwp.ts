import { apiClient } from "./client";

const v1 = "/api/v1";

export interface DwpField {
  field_key: string;
  value: string | null;
  file_url: string | null;
}

export interface DwpComment {
  id: number;
  submission_id: number;
  commented_by: number;
  comment: string;
  is_kudos: boolean;
  created_at: string;
}

export interface DwpSubmission {
  id: number;
  employee_id: number;
  template_id: number;
  type: "morning" | "eod";
  date: string;
  submitted_at: string;
  total_hours: string | null;
  mood_rating: number | null;
  linked_morning_id: number | null;
  fields: DwpField[];
  comments: DwpComment[];
}

export interface DwpTeamItem {
  submission: DwpSubmission;
  employee_code: string;
  employee_full_name: string;
}

export const dwpApi = {
  async teamToday(date?: string): Promise<DwpTeamItem[]> {
    const { data } = await apiClient.get(`${v1}/dwp/team/today`, {
      params: date ? { date } : undefined,
    });
    return data;
  },
  async teamBlockers(date?: string): Promise<DwpTeamItem[]> {
    const { data } = await apiClient.get(`${v1}/dwp/team/blockers`, {
      params: date ? { date } : undefined,
    });
    return data;
  },
  async addComment(
    submissionId: number,
    comment: string,
    isKudos: boolean,
  ): Promise<DwpComment> {
    const { data } = await apiClient.post(
      `${v1}/dwp/${submissionId}/comment`,
      { comment, is_kudos: isKudos },
    );
    return data;
  },
};
