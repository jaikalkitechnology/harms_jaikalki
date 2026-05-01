import { apiClient } from "./client";

const v1 = "/api/v1";

export interface Lead {
  id: number;
  customer_id: number | null;
  contact_name: string | null;
  contact_phone: string | null;
  contact_email: string | null;
  source: string;
  stage:
    | "new"
    | "contacted"
    | "qualified"
    | "proposal"
    | "negotiation"
    | "won"
    | "lost";
  expected_value: string;
  expected_close_date: string | null;
  assigned_to: number | null;
  score: number;
  next_action: string | null;
  next_action_date: string | null;
  notes: string | null;
  lost_reason: string | null;
  created_at: string;
}

export interface PipelineColumn {
  stage: Lead["stage"];
  leads: Lead[];
  total_value: string;
  count: number;
}

export interface Product {
  id: number;
  sku: string;
  name: string;
  description: string | null;
  category: string | null;
  unit_price: string;
  tax_pct: string;
  image_url: string | null;
  brochure_url: string | null;
  is_active: boolean;
}

export interface SalesTarget {
  id: number;
  employee_id: number;
  period_type: "monthly" | "quarterly" | "yearly";
  period_start: string;
  period_end: string;
  target_amount: string;
  achieved_amount: string;
  commission_pct: string;
  notes: string | null;
}

export interface SalesTargetSummary {
  target: SalesTarget;
  achievement_pct: number;
  commission_amount: string;
}

export interface SalesOrder {
  id: number;
  order_number: string;
  customer_id: number;
  employee_id: number;
  total_amount: string;
  status: string;
  tracking_number: string | null;
  placed_at: string;
}

export const salesApi = {
  listLeads: async (params?: { mine?: boolean; stage?: string }) => {
    const { data } = await apiClient.get<Lead[]>(`${v1}/sales/leads`, {
      params,
    });
    return data;
  },
  createLead: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<Lead>(`${v1}/sales/leads`, payload);
    return data;
  },
  updateStage: async (leadId: number, stage: string, lostReason?: string) => {
    const { data } = await apiClient.patch<Lead>(
      `${v1}/sales/leads/${leadId}/stage`,
      { stage, lost_reason: lostReason },
    );
    return data;
  },
  pipeline: async (mine = false) => {
    const { data } = await apiClient.get<PipelineColumn[]>(
      `${v1}/sales/pipeline`,
      { params: { mine } },
    );
    return data;
  },
  listProducts: async () => {
    const { data } = await apiClient.get<Product[]>(`${v1}/sales/products`);
    return data;
  },
  listTargets: async (employeeId?: number) => {
    const { data } = await apiClient.get<SalesTarget[]>(
      `${v1}/sales/targets`,
      { params: employeeId ? { employee_id: employeeId } : undefined },
    );
    return data;
  },
  createTarget: async (payload: Record<string, unknown>) => {
    const { data } = await apiClient.post<SalesTarget>(
      `${v1}/sales/targets`,
      payload,
    );
    return data;
  },
  myTarget: async () => {
    const { data } = await apiClient.get<SalesTargetSummary | null>(
      `${v1}/sales/targets/me`,
    );
    return data;
  },
  listOrders: async (params?: { mine?: boolean; status?: string }) => {
    const { data } = await apiClient.get<SalesOrder[]>(`${v1}/sales/orders`, {
      params,
    });
    return data;
  },
  setOrderStatus: async (
    orderId: number,
    status: string,
    trackingNumber?: string,
  ) => {
    const { data } = await apiClient.patch<SalesOrder>(
      `${v1}/sales/orders/${orderId}/status`,
      { status, tracking_number: trackingNumber },
    );
    return data;
  },
};
