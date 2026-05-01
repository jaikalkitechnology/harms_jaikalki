import { apiClient } from "./client";

const v1 = "/api/v1";

export interface QuestionOption {
  id: number;
  option_text: string;
  is_correct: boolean;
  sort_order: number;
}

export interface Question {
  id: number;
  question_text: string;
  question_type: string;
  department_id: number | null;
  topic: string | null;
  difficulty: string;
  language: string;
  marks: number;
  time_seconds: number;
  explanation: string | null;
  status: string;
  options: QuestionOption[];
}

export interface ExamSummary {
  id: number;
  code: string;
  title: string;
  description: string | null;
  course_id: number | null;
  exam_type: string;
  total_questions: number;
  time_limit_minutes: number;
  passing_percentage: number;
  attempts_allowed: number;
  is_published: boolean;
}

export interface CertificateVerifyResponse {
  valid: boolean;
  certificate_number: string;
  employee_name: string | null;
  title: string | null;
  issued_date: string | null;
  expiry_date: string | null;
  score_percentage: string | null;
  is_revoked: boolean;
  revoked_reason: string | null;
}

export const examApi = {
  listQuestions: async () => {
    const { data } = await apiClient.get<Question[]>(
      `${v1}/exams/questions`,
    );
    return data;
  },
  createQuestion: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<Question>(
      `${v1}/exams/questions`,
      payload,
    );
    return data;
  },
  listExams: async () => {
    const { data } = await apiClient.get<ExamSummary[]>(`${v1}/exams/`);
    return data;
  },
  publish: async (id: number, isPublished: boolean) => {
    const { data } = await apiClient.post<ExamSummary>(
      `${v1}/exams/${id}/publish`,
      { is_published: isPublished },
    );
    return data;
  },
  verify: async (certificateNumber: string) => {
    const { data } = await apiClient.get<CertificateVerifyResponse>(
      `${v1}/exams/certificates/verify/${encodeURIComponent(certificateNumber)}`,
    );
    return data;
  },
};
