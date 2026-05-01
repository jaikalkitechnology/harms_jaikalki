import { apiClient } from "./client";

const v1 = "/api/v1";

export interface Customer {
  id: number;
  name: string;
  type: "lead" | "prospect" | "customer" | "partner";
  address: string | null;
  city: string | null;
  state: string | null;
  pincode: string | null;
  geo_lat: string | null;
  geo_lng: string | null;
  industry: string | null;
  gst: string | null;
  pan: string | null;
  contact_persons: Array<Record<string, unknown>> | null;
  territory: string | null;
  is_active: boolean;
}

export interface CustomerCreate {
  name: string;
  type?: Customer["type"];
  address?: string;
  city?: string;
  state?: string;
  pincode?: string;
  geo_lat?: number;
  geo_lng?: number;
  industry?: string;
  gst?: string;
  pan?: string;
  contact_persons?: Array<Record<string, unknown>>;
  territory?: string;
}

export interface FieldJob {
  id: number;
  employee_id: number;
  customer_id: number;
  job_type: string;
  scheduled_date: string;
  scheduled_time: string | null;
  priority: "low" | "medium" | "high" | "urgent";
  status: "scheduled" | "in_progress" | "completed" | "cancelled" | "skipped";
  notes: string | null;
  assigned_at: string;
  customer: Customer | null;
}

export interface FieldJobCreate {
  employee_id: number;
  customer_id: number;
  job_type: string;
  scheduled_date: string;
  scheduled_time?: string;
  priority?: FieldJob["priority"];
  notes?: string;
}

export interface LiveMapEntry {
  employee_id: number;
  employee_code: string;
  name: string;
  lat: number;
  lng: number;
  timestamp: string;
  battery_pct: number | null;
  current_status: string;
  last_visit_customer: string | null;
}

export interface TeamPerformanceEntry {
  employee_id: number;
  employee_code: string;
  name: string;
  jobs_assigned: number;
  jobs_completed: number;
  visits_in_progress: number;
  avg_visit_minutes: number;
}

export const fieldApi = {
  listCustomers: async (params?: { search?: string; territory?: string }) => {
    const { data } = await apiClient.get<Customer[]>(`${v1}/field/customers`, {
      params,
    });
    return data;
  },
  createCustomer: async (payload: CustomerCreate) => {
    const { data } = await apiClient.post<Customer>(
      `${v1}/field/customers`,
      payload,
    );
    return data;
  },
  updateCustomer: async (id: number, payload: Partial<CustomerCreate>) => {
    const { data } = await apiClient.patch<Customer>(
      `${v1}/field/customers/${id}`,
      payload,
    );
    return data;
  },
  assignJob: async (payload: FieldJobCreate) => {
    const { data } = await apiClient.post<FieldJob>(
      `${v1}/field/jobs`,
      payload,
    );
    return data;
  },
  liveMap: async () => {
    const { data } = await apiClient.get<LiveMapEntry[]>(
      `${v1}/field/team/live-map`,
    );
    return data;
  },
  teamPerformance: async (date?: string) => {
    const { data } = await apiClient.get<TeamPerformanceEntry[]>(
      `${v1}/field/team/performance`,
      { params: date ? { date } : undefined },
    );
    return data;
  },
};
