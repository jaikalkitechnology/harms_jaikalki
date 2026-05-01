import axios, { AxiosError, type InternalAxiosRequestConfig } from "axios";
import { ADMIN_API_PREFIX, API_BASE_URL } from "@/lib/constants";

const CSRF_COOKIE = "jaikalki_csrf";

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

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const original = error.config as
      | (InternalAxiosRequestConfig & { _retry?: boolean })
      | undefined;
    const status = error.response?.status;
    const path = original?.url ?? "";
    const isAuthCall =
      path.includes("/auth/admin/login") ||
      path.includes("/auth/admin/refresh") ||
      path.includes("/auth/admin/logout");

    if (status === 401 && original && !original._retry && !isAuthCall) {
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
        window.dispatchEvent(new CustomEvent("auth:unauthorized"));
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  },
);
