import { apiClient } from "./client";
import { ADMIN_API_PREFIX } from "@/lib/constants";

const P = ADMIN_API_PREFIX;

// ── Types ────────────────────────────────────────────────────────────
export interface SystemConfig {
  id: number;
  key: string;
  value: unknown;
  category: string;
  description: string | null;
  is_secret: boolean;
  updated_at: string | null;
}

export interface Permission {
  id: number;
  code: string;
  description: string | null;
  category: string;
}

export interface Role {
  id: number;
  code: string;
  name: string;
  level: number;
  description: string | null;
  permission_codes: string[];
}

export interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  phone: string | null;
  is_active: boolean;
  is_admin_portal: boolean;
  mfa_enabled: boolean;
  role_codes: string[];
  last_login_at: string | null;
}

export interface ModuleSetting {
  id: number;
  module_code: string;
  name: string;
  description: string | null;
  is_enabled: boolean;
  is_core: boolean;
  config: Record<string, unknown> | null;
}

export interface AuditLogRow {
  id: number;
  actor_user_id: number | null;
  actor_label: string | null;
  action: string;
  entity_type: string | null;
  entity_id: string | null;
  request_id: string | null;
  ip: string | null;
  user_agent: string | null;
  method: string | null;
  path: string | null;
  status_code: number | null;
  payload: unknown;
  occurred_at: string;
}

export interface Branding {
  id: number;
  company_name: string;
  logo_url: string | null;
  favicon_url: string | null;
  primary_color: string;
  secondary_color: string;
  font_family: string;
  login_background_url: string | null;
  custom_domain: string | null;
  extras: unknown;
}

export interface DatabaseBackup {
  id: number;
  file_name: string;
  file_path: string;
  size_bytes: number;
  status: string;
  error: string | null;
  triggered_by: number | null;
  started_at: string;
  completed_at: string | null;
}

export interface ApiKey {
  id: number;
  name: string;
  key_prefix: string;
  scopes: string[] | null;
  is_active: boolean;
  expires_at: string | null;
  last_used_at: string | null;
  rate_limit_per_minute: number | null;
  created_at: string | null;
}

export interface ApiKeyCreated extends ApiKey {
  plain_key: string;
}

export interface EmailTemplate {
  id: number;
  code: string;
  name: string;
  subject: string;
  body_html: string;
  body_text: string | null;
  variables: string[] | null;
  is_active: boolean;
  updated_at: string | null;
}

// ── API ──────────────────────────────────────────────────────────────
export const superAdminApi = {
  // System config
  listConfig: async (): Promise<SystemConfig[]> =>
    (await apiClient.get(`${P}/system/config`)).data,
  upsertConfig: async (body: {
    key: string;
    value: unknown;
    category?: string;
    description?: string;
    is_secret?: boolean;
  }): Promise<SystemConfig> =>
    (await apiClient.put(`${P}/system/config`, body)).data,
  systemHealth: async (): Promise<Record<string, unknown>> =>
    (await apiClient.get(`${P}/system/health`)).data,

  // Permissions
  listPermissions: async (): Promise<Permission[]> =>
    (await apiClient.get(`${P}/permissions`)).data,
  permissionCategories: async (): Promise<string[]> =>
    (await apiClient.get(`${P}/permissions/categories`)).data,
  createPermission: async (body: {
    code: string;
    description?: string;
    category: string;
  }): Promise<Permission> =>
    (await apiClient.post(`${P}/permissions`, body)).data,
  updatePermission: async (
    id: number,
    body: { description?: string; category?: string },
  ): Promise<Permission> =>
    (await apiClient.put(`${P}/permissions/${id}`, body)).data,
  deletePermission: async (id: number): Promise<void> => {
    await apiClient.delete(`${P}/permissions/${id}`);
  },

  // Roles
  listRoles: async (): Promise<Role[]> =>
    (await apiClient.get(`${P}/roles`)).data,
  createRole: async (body: {
    code: string;
    name: string;
    level: number;
    description?: string;
    permission_codes: string[];
  }): Promise<Role> => (await apiClient.post(`${P}/roles`, body)).data,
  updateRole: async (
    id: number,
    body: { name?: string; level?: number; description?: string },
  ): Promise<Role> => (await apiClient.put(`${P}/roles/${id}`, body)).data,
  deleteRole: async (id: number): Promise<void> => {
    await apiClient.delete(`${P}/roles/${id}`);
  },
  setRolePermissions: async (
    id: number,
    permission_codes: string[],
  ): Promise<Role> =>
    (await apiClient.post(`${P}/roles/${id}/permissions`, { permission_codes }))
      .data,

  // Admins
  listAdmins: async (): Promise<AdminUser[]> =>
    (await apiClient.get(`${P}/admins`)).data,
  createAdmin: async (body: {
    email: string;
    full_name: string;
    phone?: string;
    password: string;
    role_codes: string[];
  }): Promise<AdminUser> => (await apiClient.post(`${P}/admins`, body)).data,
  updateAdmin: async (
    id: number,
    body: {
      full_name?: string;
      phone?: string;
      is_active?: boolean;
      role_codes?: string[];
      password?: string;
    },
  ): Promise<AdminUser> => (await apiClient.put(`${P}/admins/${id}`, body)).data,
  deleteAdmin: async (id: number): Promise<void> => {
    await apiClient.delete(`${P}/admins/${id}`);
  },
  setAdminRoles: async (
    id: number,
    role_codes: string[],
  ): Promise<AdminUser> =>
    (
      await apiClient.post(`${P}/admins/${id}/permissions`, {
        permission_codes: role_codes,
      })
    ).data,
  adminAudit: async (id: number): Promise<AuditLogRow[]> =>
    (await apiClient.get(`${P}/admins/${id}/audit`)).data,

  // Modules
  listModules: async (): Promise<ModuleSetting[]> =>
    (await apiClient.get(`${P}/modules`)).data,
  updateModule: async (
    id: number,
    body: { is_enabled?: boolean; config?: unknown },
  ): Promise<ModuleSetting> =>
    (await apiClient.put(`${P}/modules/${id}`, body)).data,

  // Audit logs (super-admin scope)
  listAuditLogs: async (params: {
    actor_user_id?: number;
    action?: string;
    entity_type?: string;
    entity_id?: string;
    since_days?: number;
    limit?: number;
  } = {}): Promise<AuditLogRow[]> =>
    (await apiClient.get(`${P}/audit-logs`, { params })).data,

  // Branding
  getBranding: async (): Promise<Branding> =>
    (await apiClient.get(`${P}/branding`)).data,
  updateBranding: async (body: Partial<Branding>): Promise<Branding> =>
    (await apiClient.put(`${P}/branding`, body)).data,

  // Backups
  listBackups: async (): Promise<DatabaseBackup[]> =>
    (await apiClient.get(`${P}/backups`)).data,
  triggerBackup: async (): Promise<DatabaseBackup> =>
    (await apiClient.post(`${P}/backups`)).data,

  // API keys
  listApiKeys: async (): Promise<ApiKey[]> =>
    (await apiClient.get(`${P}/api-keys`)).data,
  createApiKey: async (body: {
    name: string;
    scopes: string[];
    expires_at?: string | null;
    rate_limit_per_minute?: number | null;
  }): Promise<ApiKeyCreated> =>
    (await apiClient.post(`${P}/api-keys`, body)).data,
  revokeApiKey: async (id: number): Promise<void> => {
    await apiClient.delete(`${P}/api-keys/${id}`);
  },

  // Leave policy
  getLeavePolicy: async (): Promise<{
    sandwich_enabled: boolean;
    sandwich_count_holidays: boolean;
    earned_accrual_enabled: boolean;
    earned_accrual_days_required: number;
    earned_accrual_credit_days: number;
    earned_accrual_leave_type_code: string;
  }> => (await apiClient.get(`${P}/leave-policy`)).data,
  setLeavePolicy: async (body: Record<string, unknown>) =>
    (await apiClient.put(`${P}/leave-policy`, body)).data,
  recomputeEarnedLeaves: async (): Promise<{
    enabled: boolean;
    processed: number;
    credited_total: number;
    error?: string;
  }> =>
    (await apiClient.post(`${P}/leave-policy/recompute-earned-leaves`)).data,

  // Office geo-fence
  getOfficeLocation: async (): Promise<{
    lat: number;
    lng: number;
    radius_m: number;
  }> => (await apiClient.get(`${P}/office-location`)).data,
  setOfficeLocation: async (body: {
    lat: number;
    lng: number;
    radius_m: number;
  }): Promise<{ lat: number; lng: number; radius_m: number }> =>
    (await apiClient.put(`${P}/office-location`, body)).data,

  // Email templates
  listEmailTemplates: async (): Promise<EmailTemplate[]> =>
    (await apiClient.get(`${P}/email-templates`)).data,
  createEmailTemplate: async (body: {
    code: string;
    name: string;
    subject: string;
    body_html: string;
    body_text?: string;
    variables: string[];
    is_active: boolean;
  }): Promise<EmailTemplate> =>
    (await apiClient.post(`${P}/email-templates`, body)).data,
  updateEmailTemplate: async (
    id: number,
    body: Partial<EmailTemplate>,
  ): Promise<EmailTemplate> =>
    (await apiClient.put(`${P}/email-templates/${id}`, body)).data,
  deleteEmailTemplate: async (id: number): Promise<void> => {
    await apiClient.delete(`${P}/email-templates/${id}`);
  },
  testEmailTemplate: async (
    id: number,
    body: { to_email: string; sample_variables: Record<string, unknown> },
  ): Promise<{ sent: boolean }> =>
    (await apiClient.post(`${P}/email-templates/${id}/test`, body)).data,
};
