import { apiClient } from "./client";
import { ADMIN_API_PREFIX } from "@/lib/constants";

export interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  phone: string | null;
  is_active: boolean;
  is_admin_portal: boolean;
  mfa_enabled: boolean;
  last_login_at: string | null;
}

export interface MeResponse {
  user: AdminUser;
  role: string | null;
  role_level: number;
  roles: string[];
  permissions: string[];
}

export async function adminLogin(payload: {
  email: string;
  password: string;
  remember_me?: boolean;
  mfa_code?: string;
}): Promise<MeResponse> {
  const { data } = await apiClient.post<MeResponse>(
    `${ADMIN_API_PREFIX}/auth/login`,
    payload,
  );
  return data;
}

export async function adminLogout(): Promise<void> {
  await apiClient.post(`${ADMIN_API_PREFIX}/auth/logout`);
}

export async function adminMe(): Promise<MeResponse> {
  const { data } = await apiClient.get<MeResponse>(
    `${ADMIN_API_PREFIX}/auth/me`,
  );
  return data;
}

export async function adminRefresh(): Promise<MeResponse> {
  const { data } = await apiClient.post<MeResponse>(
    `${ADMIN_API_PREFIX}/auth/refresh`,
  );
  return data;
}

export async function listPermissions(): Promise<
  Array<{ id: number; code: string; description: string | null; category: string }>
> {
  const { data } = await apiClient.get(`${ADMIN_API_PREFIX}/permissions`);
  return data;
}
