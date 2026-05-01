import { apiClient } from "./client";

const v1 = "/api/v1";

export interface Asset {
  id: number;
  asset_tag: string;
  name: string;
  category: string;
  serial_number: string | null;
  purchase_date: string | null;
  purchase_cost: string | null;
  warranty_until: string | null;
  condition: string;
  status: string;
  assigned_to: number | null;
  assigned_at: string | null;
  notes: string | null;
}

export interface Visitor {
  id: number;
  full_name: string;
  contact_phone: string | null;
  contact_email: string | null;
  company: string | null;
  purpose: string;
  host_employee_id: number;
  expected_at: string;
  qr_token: string;
  checked_in_at: string | null;
  checked_out_at: string | null;
  badge_number: string | null;
  status: string;
}

export interface MeetingRoom {
  id: number;
  code: string;
  name: string;
  location: string | null;
  capacity: number;
  has_video: boolean;
  has_whiteboard: boolean;
  is_active: boolean;
}

export interface RoomBooking {
  id: number;
  room_id: number;
  booked_by_employee_id: number;
  title: string;
  start_time: string;
  end_time: string;
  attendees: string[] | null;
  status: string;
  notes: string | null;
}

export interface JobPosting {
  id: number;
  code: string;
  title: string;
  department_id: number | null;
  location: string | null;
  employment_type: string;
  description: string | null;
  requirements: string | null;
  referral_bonus: string | null;
  is_internal_only: boolean;
  posted_at: string;
  closes_on: string | null;
  status: string;
}

export interface JobApplication {
  id: number;
  posting_id: number;
  applicant_employee_id: number | null;
  external_applicant_name: string | null;
  external_applicant_email: string | null;
  referrer_employee_id: number | null;
  cover_note: string | null;
  resume_url: string | null;
  status: string;
  referral_bonus_paid: boolean;
  submitted_at: string;
}

export const polishApi = {
  listAssets: async (params?: { status?: string }) => {
    const { data } = await apiClient.get<Asset[]>(`${v1}/polish/assets`, {
      params,
    });
    return data;
  },
  createAsset: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<Asset>(
      `${v1}/polish/assets`,
      payload,
    );
    return data;
  },
  assignAsset: async (id: number, employeeId: number, notes?: string) => {
    const { data } = await apiClient.post<Asset>(
      `${v1}/polish/assets/${id}/assign`,
      { employee_id: employeeId, notes },
    );
    return data;
  },
  returnAsset: async (
    id: number,
    returnCondition: string,
    notes?: string,
  ) => {
    const { data } = await apiClient.post<Asset>(
      `${v1}/polish/assets/${id}/return`,
      { return_condition: returnCondition, notes },
    );
    return data;
  },
  todayVisitors: async () => {
    const { data } = await apiClient.get<Visitor[]>(
      `${v1}/polish/visitors/today`,
    );
    return data;
  },
  visitorCheckIn: async (qrToken: string, badgeNumber?: string) => {
    const { data } = await apiClient.post<Visitor>(
      `${v1}/polish/visitors/check-in`,
      { qr_token: qrToken, badge_number: badgeNumber },
    );
    return data;
  },
  visitorCheckOut: async (visitorId: number) => {
    const { data } = await apiClient.post<Visitor>(
      `${v1}/polish/visitors/${visitorId}/check-out`,
    );
    return data;
  },
  listRooms: async () => {
    const { data } = await apiClient.get<MeetingRoom[]>(`${v1}/polish/rooms`);
    return data;
  },
  createRoom: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<MeetingRoom>(
      `${v1}/polish/rooms`,
      payload,
    );
    return data;
  },
  listBookings: async (params?: { room_id?: number; upcoming_only?: boolean }) => {
    const { data } = await apiClient.get<RoomBooking[]>(
      `${v1}/polish/rooms/bookings`,
      { params },
    );
    return data;
  },
  listPostings: async (params?: { status?: string }) => {
    const { data } = await apiClient.get<JobPosting[]>(`${v1}/polish/jobs`, {
      params,
    });
    return data;
  },
  createPosting: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<JobPosting>(
      `${v1}/polish/jobs`,
      payload,
    );
    return data;
  },
  setPostingStatus: async (id: number, status: string) => {
    const { data } = await apiClient.patch<JobPosting>(
      `${v1}/polish/jobs/${id}/status`,
      { status },
    );
    return data;
  },
  applicationsForPosting: async (id: number) => {
    const { data } = await apiClient.get<JobApplication[]>(
      `${v1}/polish/jobs/${id}/applications`,
    );
    return data;
  },
  setApplicationStatus: async (id: number, status: string) => {
    const { data } = await apiClient.patch<JobApplication>(
      `${v1}/polish/jobs/applications/${id}/status`,
      { status },
    );
    return data;
  },
};
