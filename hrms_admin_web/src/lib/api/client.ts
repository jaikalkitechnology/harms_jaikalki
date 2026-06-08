import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { ADMIN_API_PREFIX, API_BASE_URL } from "@/lib/constants";

const CSRF_COOKIE = "jaikalki_csrf";
// Set by the auth store once a login succeeds, removed on logout / wipe.
// The 401 interceptor uses this to decide whether a silent-refresh +
// auth:unauthorized broadcast is appropriate. Without it, the first /me
// 401 on a fresh page load races with a fast manual sign-in and wipes
// the freshly-set session — the "have to click sign-in twice" symptom.
const AUTH_ACTIVE_KEY = "jaikalki_auth_active";

export function markAuthActive(): void {
  try {
    sessionStorage.setItem(AUTH_ACTIVE_KEY, "1");
  } catch {
    /* private mode etc. — fall back to no-op */
  }
}

export function clearAuthActive(): void {
  try {
    sessionStorage.removeItem(AUTH_ACTIVE_KEY);
  } catch {
    /* ignore */
  }
}

function isAuthActive(): boolean {
  try {
    return sessionStorage.getItem(AUTH_ACTIVE_KEY) === "1";
  } catch {
    return false;
  }
}

function readCookie(name: string): string | null {
  const match = document.cookie.match(
    new RegExp(`(?:^|; )${name}=([^;]+)`),
  );
  return match ? decodeURIComponent(match[1]) : null;
}

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true,
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.request.use((config) => {
  const method = (config.method ?? "get").toLowerCase();
  if (!["get", "head", "options"].includes(method)) {
    const csrf = readCookie(CSRF_COOKIE);
    if (csrf) {
      config.headers["X-CSRF-Token"] = csrf;
    }
  }
  return config;
});

let refreshing: Promise<void> | null = null;

// Recognise the admin auth endpoints so a 401 from them isn't treated
// like a generic session expiry. Earlier these patterns were inverted
// ("/auth/admin/login" vs the real "/admin/auth/login"), which made
// every login or refresh failure cascade into another refresh + an
// auth:unauthorized broadcast.
const AUTH_PATHS = [
  `${ADMIN_API_PREFIX}/auth/login`,
  `${ADMIN_API_PREFIX}/auth/refresh`,
  `${ADMIN_API_PREFIX}/auth/logout`,
  `${ADMIN_API_PREFIX}/auth/me`,
];

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;
    const status = error.response?.status;
    const path = original?.url ?? "";
    const isAuthCall = AUTH_PATHS.some((p) => path.includes(p));

    if (status === 401 && original && !original._retry && !isAuthCall) {
      // Don't attempt a silent refresh when the page has no active
      // session — that's just an unauthenticated user hitting a guarded
      // endpoint. Let the caller (e.g. checkAuth) handle it.
      if (!isAuthActive()) {
        return Promise.reject(error);
      }
      original._retry = true;
      try {
        if (!refreshing) {
          refreshing = apiClient
            .post(`${ADMIN_API_PREFIX}/auth/refresh`)
            .then(() => undefined)
            .finally(() => {
              refreshing = null;
            });
        }
        await refreshing;
        return apiClient.request(original);
      } catch {
        clearAuthActive();
        window.dispatchEvent(new CustomEvent("auth:unauthorized"));
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  },
);
