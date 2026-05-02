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

// ── Account / security (uses /api/v1/auth — same cookie session) ────
const V1 = "/api/v1";

export async function changePassword(body: {
  old_password: string;
  new_password: string;
}): Promise<void> {
  await apiClient.post(`${V1}/auth/change-password`, body);
}

export interface MfaEnrollResponse {
  secret: string;
  otpauth_uri: string;
}

export async function mfaEnroll(): Promise<MfaEnrollResponse> {
  const { data } = await apiClient.post<MfaEnrollResponse>(
    `${V1}/auth/mfa/enroll`,
  );
  return data;
}

export async function mfaVerify(code: string): Promise<{ backup_codes: string[] }> {
  const { data } = await apiClient.post<{ backup_codes: string[] }>(
    `${V1}/auth/mfa/verify`,
    { code },
  );
  return data;
}

export async function mfaDisable(code: string): Promise<void> {
  await apiClient.post(`${V1}/auth/mfa/disable`, { code });
}
