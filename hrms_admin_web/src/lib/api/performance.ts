import { apiClient } from "./client";

const v1 = "/api/v1";

export interface ReviewCycle {
  id: number;
  code: string;
  name: string;
  cycle_type: string;
  period_start: string;
  period_end: string;
  self_review_due: string | null;
  manager_review_due: string | null;
  calibration_due: string | null;
  status: string;
}

export interface Goal {
  id: number;
  employee_id: number;
  cycle_id: number | null;
  title: string;
  description: string | null;
  metric: string | null;
  target_value: string | null;
  weight_pct: number;
  progress_pct: number;
  category: string;
  status: string;
  due_date: string | null;
}

export interface PerformanceReview {
  id: number;
  cycle_id: number;
  employee_id: number;
  review_type: string;
  reviewer_id: number | null;
  overall_rating: string | null;
  achievements: string | null;
  improvement_areas: string | null;
  recommendations: string | null;
  increment_recommendation_pct: number | null;
  status: string;
  submitted_at: string | null;
  acknowledged_at: string | null;
}

export interface FeedbackAggregate {
  subject_employee_id: number;
  response_count: number;
  avg_rating: number;
  competency_averages: Record<string, number>;
  anonymous_strengths: string[];
  anonymous_improvements: string[];
}

export const performanceApi = {
  shareReview: async (reviewId: number) => {
    const { data } = await apiClient.post<PerformanceReview>(
      `${v1}/performance/reviews/${reviewId}/share`,
    );
    return data;
  },
  aggregateFeedback: async (employeeId: number, cycleId?: number) => {
    const { data } = await apiClient.get<FeedbackAggregate>(
      `${v1}/performance/feedback/aggregate/${employeeId}`,
      { params: cycleId ? { cycle_id: cycleId } : undefined },
    );
    return data;
  },
  requestFeedback: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post(
      `${v1}/performance/feedback/requests`,
      payload,
    );
    return data;
  },
};
