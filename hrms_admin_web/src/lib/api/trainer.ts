import { apiClient } from "./client";

const v1 = "/api/v1";

export interface Trainer {
  id: number;
  employee_id: number | null;
  is_external: boolean;
  full_name: string;
  bio: string | null;
  headline: string | null;
  contact_email: string | null;
  contact_phone: string | null;
  profile_photo_url: string | null;
  languages: string[] | null;
  specializations: string[] | null;
  years_experience: number;
  hourly_rate: string | null;
  rating_average: string;
  sessions_completed: number;
  is_active: boolean;
}

export interface TrainingSession {
  id: number;
  code: string;
  title: string;
  description: string | null;
  trainer_id: number;
  course_id: number | null;
  department_id: number | null;
  session_type: string;
  scheduled_start: string;
  scheduled_end: string;
  timezone: string;
  location: string | null;
  meeting_url: string | null;
  capacity: number;
  qr_token: string | null;
  recording_url: string | null;
  status: string;
  participants_count: number;
}

export interface TrainerAnalytics {
  trainer_id: number;
  full_name: string;
  sessions_completed: number;
  upcoming_sessions: number;
  total_participants: number;
  avg_rating: number;
  review_count: number;
  attendance_rate: number;
}

export const trainerApi = {
  listTrainers: async (params?: {
    search?: string;
    specialization?: string;
    is_external?: boolean;
    include_inactive?: boolean;
  }) => {
    const { data } = await apiClient.get<Trainer[]>(
      `${v1}/trainer/trainers`,
      { params },
    );
    return data;
  },
  createTrainer: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<Trainer>(
      `${v1}/trainer/trainers`,
      payload,
    );
    return data;
  },
  updateTrainer: async (id: number, payload: Record<string, unknown>) => {
    const { data } = await apiClient.put<Trainer>(
      `${v1}/trainer/trainers/${id}`,
      payload,
    );
    return data;
  },
  deleteTrainer: async (id: number) => {
    await apiClient.delete(`${v1}/trainer/trainers/${id}`);
  },
  analytics: async (trainerId: number) => {
    const { data } = await apiClient.get<TrainerAnalytics>(
      `${v1}/trainer/trainers/${trainerId}/analytics`,
    );
    return data;
  },
  listSessions: async (params?: {
    trainer_id?: number;
    upcoming_only?: boolean;
    status?: string;
    search?: string;
  }) => {
    const { data } = await apiClient.get<TrainingSession[]>(
      `${v1}/trainer/sessions`,
      { params },
    );
    return data;
  },
  createSession: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<TrainingSession>(
      `${v1}/trainer/sessions`,
      payload,
    );
    return data;
  },
  updateSession: async (id: number, payload: Record<string, unknown>) => {
    const { data } = await apiClient.put<TrainingSession>(
      `${v1}/trainer/sessions/${id}`,
      payload,
    );
    return data;
  },
  setStatus: async (id: number, status: string) => {
    const { data } = await apiClient.patch<TrainingSession>(
      `${v1}/trainer/sessions/${id}/status`,
      { status },
    );
    return data;
  },
};
