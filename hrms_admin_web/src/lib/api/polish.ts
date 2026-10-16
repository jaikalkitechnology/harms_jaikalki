import { apiClient } from "./client";

const v1 = "/api/v1";

export type AssetCondition = "working" | "damaged" | "not_working" | "expired";
export type AssetStatus = "in_stock" | "assigned" | "in_repair" | "lost" | "retired";

export interface Asset {
  id: number;
  asset_tag: string;
  name: string;
  category: string;
  brand: string | null;
  model: string | null;
  specs: Record<string, string> | null;
  /** Accessory of this asset (e.g. a laptop's charger). */
  parent_asset_id: number | null;
  serial_number: string | null;
  purchase_date: string | null;
  purchase_cost: string | null;
  warranty_until: string | null;
  condition: AssetCondition;
  /** Only working assets can be handed out. */
  is_usable: boolean;
  status: AssetStatus;
  assigned_to: number | null;
  assigned_at: string | null;
  notes: string | null;
}

export interface AssetSpecField {
  key: string;
  label: string;
}

export interface AssetCategory {
  id: number;
  code: string;
  name: string;
  is_accessory: boolean;
  spec_fields: AssetSpecField[] | null;
  sort_order: number;
  is_active: boolean;
}

export interface AssetCategoryInput {
  name: string;
  is_accessory: boolean;
  spec_fields: { label: string; key?: string }[];
  is_active?: boolean;
}

export interface AssetSummary {
  total: number;
  in_stock_usable: number;
  assigned: number;
  not_usable: number;
  in_repair: number;
  lost: number;
  retired: number;
}

export interface AssetAssignment {
  id: number;
  asset_id: number;
  employee_id: number;
  assigned_at: string;
  returned_at: string | null;
  return_condition: string | null;
  notes: string | null;
  assigned_by: number | null;
  received_by: number | null;
}

export interface EmployeeAssets {
  current: Asset[];
  history: (AssetAssignment & { asset: Asset })[];
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
  published_to_app: boolean;
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
  assetCategories: async (includeInactive = false) => {
    const { data } = await apiClient.get<AssetCategory[]>(
      `${v1}/polish/asset-categories`,
      { params: { include_inactive: includeInactive } },
    );
    return data;
  },
  createAssetCategory: async (payload: AssetCategoryInput) => {
    const { data } = await apiClient.post<AssetCategory>(
      `${v1}/polish/asset-categories`,
      payload,
    );
    return data;
  },
  updateAssetCategory: async (id: number, payload: Partial<AssetCategoryInput>) => {
    const { data } = await apiClient.put<AssetCategory>(
      `${v1}/polish/asset-categories/${id}`,
      payload,
    );
    return data;
  },
  assetSummary: async () => {
    const { data } = await apiClient.get<AssetSummary>(`${v1}/polish/assets/summary`);
    return data;
  },
  listAssets: async (params?: {
    status?: string;
    category?: string;
    condition?: string;
    usable?: boolean;
    assigned_to?: number;
    search?: string;
  }) => {
    const { data } = await apiClient.get<Asset[]>(`${v1}/polish/assets`, {
      params,
    });
    return data;
  },
  assetHistory: async (id: number) => {
    const { data } = await apiClient.get<AssetAssignment[]>(
      `${v1}/polish/assets/${id}/history`,
    );
    return data;
  },
  employeeAssets: async (employeeId: number) => {
    const { data } = await apiClient.get<EmployeeAssets>(
      `${v1}/polish/assets/employee/${employeeId}`,
    );
    return data;
  },
  createAsset: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<Asset>(
      `${v1}/polish/assets`,
      payload,
    );
    return data;
  },
  updateAsset: async (id: number, payload: Record<string, unknown>) => {
    const { data } = await apiClient.put<Asset>(
      `${v1}/polish/assets/${id}`,
      payload,
    );
    return data;
  },
  assignAsset: async (
    id: number,
    employeeId: number,
    opts: { notes?: string; includeAccessories?: boolean } = {},
  ) => {
    const { data } = await apiClient.post<Asset>(
      `${v1}/polish/assets/${id}/assign`,
      {
        employee_id: employeeId,
        notes: opts.notes || null,
        include_accessories: opts.includeAccessories ?? true,
      },
    );
    return data;
  },
  /** No longer available (sold, scrapped, end of life…); history kept. */
  retireAsset: async (id: number, reason: string, notes?: string) => {
    const { data } = await apiClient.post<Asset>(
      `${v1}/polish/assets/${id}/retire`,
      { reason, notes: notes || null },
    );
    return data;
  },
  restoreAsset: async (id: number) => {
    const { data } = await apiClient.post<Asset>(`${v1}/polish/assets/${id}/restore`);
    return data;
  },
  /** Only for assets never handed to anyone (e.g. added by mistake). */
  deleteAsset: async (id: number) => {
    await apiClient.delete(`${v1}/polish/assets/${id}`);
  },
  returnAsset: async (
    id: number,
    returnCondition: string,
    opts: { notes?: string; includeAccessories?: boolean } = {},
  ) => {
    const { data } = await apiClient.post<Asset>(
      `${v1}/polish/assets/${id}/return`,
      {
        return_condition: returnCondition,
        notes: opts.notes || null,
        include_accessories: opts.includeAccessories ?? true,
      },
    );
    return data;
  },
  todayVisitors: async () => {
    const { data } = await apiClient.get<Visitor[]>(
      `${v1}/polish/visitors/today`,
    );
    return data;
  },
  listVisitors: async (params?: {
    status?: string;
    host_employee_id?: number;
    search?: string;
    from_date?: string;
    to_date?: string;
  }) => {
    const { data } = await apiClient.get<Visitor[]>(
      `${v1}/polish/visitors`,
      { params },
    );
    return data;
  },
  visitorByToken: async (qrToken: string) => {
    const { data } = await apiClient.get<Visitor>(
      `${v1}/polish/visitors/by-token/${encodeURIComponent(qrToken)}`,
    );
    return data;
  },
  preRegisterVisitor: async (payload: {
    full_name: string;
    contact_phone?: string | null;
    contact_email?: string | null;
    company?: string | null;
    purpose: string;
    expected_at: string;
  }) => {
    const { data } = await apiClient.post<Visitor>(
      `${v1}/polish/visitors`,
      payload,
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
  visitorCheckOutByToken: async (qrToken: string) => {
    const { data } = await apiClient.post<Visitor>(
      `${v1}/polish/visitors/by-token/${encodeURIComponent(qrToken)}/check-out`,
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
  listPostings: async (params?: {
    status?: string;
    search?: string;
    published_to_app?: boolean;
  }) => {
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
  updatePosting: async (id: number, payload: Record<string, unknown>) => {
    const { data } = await apiClient.put<JobPosting>(
      `${v1}/polish/jobs/${id}`,
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
