import { apiClient } from "./client";

const v1 = "/api/v1";

export interface CourseSummary {
  id: number;
  code: string;
  title: string;
  description: string | null;
  category: string;
  difficulty: string;
  estimated_hours: number;
  is_mandatory: boolean;
  points: number;
  thumbnail_url: string | null;
  department_id: number | null;
  is_published: boolean;
  question_count: number;
  exam_count: number;
}

export interface Lesson {
  id: number;
  module_id: number;
  title: string;
  content_type: string;
  content_url: string | null;
  article_body: string | null;
  duration_minutes: number;
  sort_order: number;
  points: number;
}

export interface CourseModule {
  id: number;
  course_id: number;
  title: string;
  description: string | null;
  sort_order: number;
  lessons: Lesson[];
}

export interface Course extends CourseSummary {
  department_id: number | null;
  validity_months: number | null;
  is_published: boolean;
  modules: CourseModule[];
}

export interface Enrollment {
  id: number;
  employee_id: number;
  course_id: number;
  enrolled_at: string;
  due_date: string | null;
  status: string;
  progress_percentage: number;
  completed_at: string | null;
  score: number | null;
}

export interface LeaderboardEntry {
  employee_id: number;
  employee_code: string;
  name: string;
  points: number;
  courses_completed: number;
  level: string;
  streak_days: number;
}

export interface ComplianceRow {
  course_id: number;
  course_code: string;
  title: string;
  category: string;
  status: string;
  progress_percentage: number;
  completed_at: string | null;
  next_due_at: string | null;
}

export interface CourseRich extends CourseSummary {
  validity_months: number | null;
}

export const lmsApi = {
  listCourses: async (params?: {
    category?: string;
    department_id?: number;
    include_unpublished?: boolean;
  }) => {
    const { data } = await apiClient.get<CourseRich[]>(
      `${v1}/lms/courses`,
      { params },
    );
    return data;
  },
  mandatory: async () => {
    const { data } = await apiClient.get<CourseSummary[]>(
      `${v1}/lms/courses/mandatory`,
    );
    return data;
  },
  getCourse: async (id: number) => {
    const { data } = await apiClient.get<Course>(`${v1}/lms/courses/${id}`);
    return data;
  },
  createCourse: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<Course>(
      `${v1}/lms/courses`,
      payload,
    );
    return data;
  },
  publish: async (id: number, isPublished: boolean) => {
    const { data } = await apiClient.post<Course>(
      `${v1}/lms/courses/${id}/publish`,
      { is_published: isPublished },
    );
    return data;
  },
  updateCourse: async (id: number, payload: Record<string, unknown>) => {
    const { data } = await apiClient.put<Course>(
      `${v1}/lms/courses/${id}`,
      payload,
    );
    return data;
  },
  deleteCourse: async (id: number) => {
    await apiClient.delete(`${v1}/lms/courses/${id}`);
  },
  adminEnroll: async (courseId: number, employeeId: number, dueDate?: string) => {
    const { data } = await apiClient.post<Enrollment>(`${v1}/lms/enroll`, {
      course_id: courseId,
      employee_id: employeeId,
      due_date: dueDate,
    });
    return data;
  },
  leaderboard: async () => {
    const { data } = await apiClient.get<LeaderboardEntry[]>(
      `${v1}/lms/leaderboard`,
    );
    return data;
  },
  myCompliance: async () => {
    const { data } = await apiClient.get<ComplianceRow[]>(
      `${v1}/lms/compliance/me`,
    );
    return data;
  },
};
