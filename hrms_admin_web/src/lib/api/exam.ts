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
  course_id: number | null;
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
  department_id?: number | null;
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

export type CertificateType =
  | "achievement"
  | "appreciation"
  | "completion"
  | "participation"
  | "excellence"
  | "training"
  | "custom";

export interface Certificate {
  id: number;
  certificate_number: string;
  employee_id: number;
  course_id: number | null;
  exam_attempt_id: number | null;
  title: string;
  certificate_type: CertificateType | null;
  body_text: string | null;
  issued_date: string;
  expiry_date: string | null;
  score_percentage: string | null;
  pdf_url: string | null;
  is_revoked: boolean;
  revoked_reason: string | null;
}

export const examApi = {
  listQuestions: async (params?: {
    department_id?: number;
    course_id?: number;
    topic?: string;
    difficulty?: string;
    status?: string;
  }) => {
    const { data } = await apiClient.get<Question[]>(
      `${v1}/exams/questions`,
      { params },
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
  updateQuestion: async (id: number, payload: Record<string, unknown>) => {
    const { data } = await apiClient.put<Question>(
      `${v1}/exams/questions/${id}`,
      payload,
    );
    return data;
  },
  deleteQuestion: async (id: number) => {
    await apiClient.delete(`${v1}/exams/questions/${id}`);
  },
  replaceQuestionOptions: async (
    id: number,
    options: { option_text: string; is_correct: boolean; sort_order: number }[],
  ) => {
    const { data } = await apiClient.put<Question>(
      `${v1}/exams/questions/${id}/options`,
      { options },
    );
    return data;
  },
  listExams: async (params?: {
    course_id?: number;
    exam_type?: string;
    include_unpublished?: boolean;
  }) => {
    const { data } = await apiClient.get<ExamSummary[]>(`${v1}/exams/`, {
      params,
    });
    return data;
  },
  createExam: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<ExamSummary>(
      `${v1}/exams/`,
      payload,
    );
    return data;
  },
  updateExam: async (id: number, payload: Record<string, unknown>) => {
    const { data } = await apiClient.put<ExamSummary>(
      `${v1}/exams/${id}`,
      payload,
    );
    return data;
  },
  deleteExam: async (id: number) => {
    await apiClient.delete(`${v1}/exams/${id}`);
  },
  publish: async (id: number, isPublished: boolean) => {
    const { data } = await apiClient.post<ExamSummary>(
      `${v1}/exams/${id}/publish`,
      { is_published: isPublished },
    );
    return data;
  },
  setExamQuestions: async (id: number, questionIds: number[]) => {
    const { data } = await apiClient.post(
      `${v1}/exams/${id}/questions/bulk`,
      { question_ids: questionIds },
    );
    return data;
  },
  verify: async (certificateNumber: string) => {
    const { data } = await apiClient.get<CertificateVerifyResponse>(
      `${v1}/exams/certificates/verify/${encodeURIComponent(certificateNumber)}`,
    );
    return data;
  },
  listCertificates: async (params?: {
    employee_id?: number;
    course_id?: number;
    is_revoked?: boolean;
    search?: string;
    from_date?: string;
    to_date?: string;
    limit?: number;
    offset?: number;
  }) => {
    const { data } = await apiClient.get<Certificate[]>(
      `${v1}/exams/certificates`,
      { params },
    );
    return data;
  },
  issueCertificate: async (payload: {
    employee_id: number;
    title: string;
    certificate_type?: CertificateType;
    body_text?: string | null;
    course_id?: number | null;
    exam_attempt_id?: number | null;
    issued_date?: string;
    expiry_date?: string | null;
    score_percentage?: number | null;
  }) => {
    const { data } = await apiClient.post<Certificate>(
      `${v1}/exams/certificates`,
      payload,
    );
    return data;
  },
  updateCertificate: async (
    id: number,
    payload: {
      title?: string;
      certificate_type?: CertificateType;
      body_text?: string | null;
      issued_date?: string;
      expiry_date?: string | null;
      score_percentage?: number | null;
      course_id?: number | null;
    },
  ) => {
    const { data } = await apiClient.put<Certificate>(
      `${v1}/exams/certificates/${id}`,
      payload,
    );
    return data;
  },
  revokeCertificate: async (id: number, reason: string) => {
    const { data } = await apiClient.post<Certificate>(
      `${v1}/exams/certificates/${id}/revoke`,
      { reason },
    );
    return data;
  },
  restoreCertificate: async (id: number) => {
    const { data } = await apiClient.post<Certificate>(
      `${v1}/exams/certificates/${id}/restore`,
    );
    return data;
  },
  certificatePdfUrl: (id: number) => `${v1}/exams/certificates/${id}/pdf`,
  myCertificates: async () => {
    const { data } = await apiClient.get<Certificate[]>(
      `${v1}/exams/me/certificates`,
    );
    return data;
  },
};
