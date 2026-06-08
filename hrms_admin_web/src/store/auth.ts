import { create } from "zustand";
import {
  adminLogin,
  adminLogout,
  adminMe,
  type AdminUser,
} from "@/lib/api/auth";
import { clearAuthActive, markAuthActive } from "@/lib/api/client";
import type { Role } from "@/lib/constants";

interface AuthState {
  user: AdminUser | null;
  role: Role | null;
  roles: Role[];
  permissions: string[];
  roleLevel: number;
  isAuthenticated: boolean;
  isLoading: boolean;
  needsMfa: boolean;
  pendingCredentials: { email: string; password: string; rememberMe: boolean } | null;

  login: (email: string, password: string, rememberMe?: boolean) => Promise<void>;
  submitMfa: (code: string) => Promise<void>;
  cancelMfa: () => void;
  logout: () => Promise<void>;
  checkAuth: () => Promise<void>;
  hasPermission: (permission: string) => boolean;
  hasRole: (role: Role) => boolean;
  hasAnyRole: (roles: Role[]) => boolean;
}

function applyMe(
  set: (partial: Partial<AuthState>) => void,
  data: Awaited<ReturnType<typeof adminMe>>,
) {
  markAuthActive();
  set({
    user: data.user,
    role: (data.role as Role | null) ?? null,
    roles: (data.roles ?? []) as Role[],
    permissions: data.permissions ?? [],
    roleLevel: data.role_level ?? 0,
    isAuthenticated: true,
    isLoading: false,
    needsMfa: false,
    pendingCredentials: null,
  });
}

const initial = {
  user: null,
  role: null,
  roles: [],
  permissions: [],
  roleLevel: 0,
  isAuthenticated: false,
  needsMfa: false,
  pendingCredentials: null,
};

export const useAuthStore = create<AuthState>((set, get) => ({
  ...initial,
  isLoading: true,

  login: async (email, password, rememberMe = false) => {
    try {
      const data = await adminLogin({ email, password, remember_me: rememberMe });
      applyMe(set, data);
    } catch (err: unknown) {
      const detail =
        (err as { response?: { data?: { detail?: string } } })?.response?.data
          ?.detail ?? "";
      if (detail.toLowerCase().includes("mfa")) {
        set({
          needsMfa: true,
          pendingCredentials: { email, password, rememberMe },
        });
      }
      throw err;
    }
  },

  submitMfa: async (code) => {
    const pending = get().pendingCredentials;
    if (!pending) {
      throw new Error("No pending login");
    }
    const data = await adminLogin({
      email: pending.email,
      password: pending.password,
      remember_me: pending.rememberMe,
      mfa_code: code,
    });
    applyMe(set, data);
  },

  cancelMfa: () => set({ needsMfa: false, pendingCredentials: null }),

  logout: async () => {
    try {
      await adminLogout();
    } catch {
      /* ignore */
    }
    clearAuthActive();
    set({ ...initial, isLoading: false });
  },

  checkAuth: async () => {
    set({ isLoading: true });
    try {
      const data = await adminMe();
      applyMe(set, data);
    } catch {
      // Don't clear `auth_active` here: a fresh page load with no
      // session is the normal case, and a transient 401 on a real
      // session expiry is handled by the interceptor.
      set({ ...initial, isLoading: false });
    }
  },

  hasPermission: (permission) => {
    const { role, permissions } = get();
    if (role === "super_admin") return true;
    return permissions.includes(permission);
  },

  hasRole: (role) => get().roles.includes(role),

  hasAnyRole: (roles) => {
    const userRoles = get().roles;
    return roles.some((r) => userRoles.includes(r));
  },
}));

if (typeof window !== "undefined") {
  window.addEventListener("auth:unauthorized", () => {
    clearAuthActive();
    useAuthStore.setState({ ...initial, isLoading: false });
  });
}
