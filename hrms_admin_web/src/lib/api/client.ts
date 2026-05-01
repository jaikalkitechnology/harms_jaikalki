import axios, { AxiosError } from "axios";
import { API_BASE_URL } from "@/lib/constants";

export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  withCredentials: true, // httpOnly cookie auth (admin)
  headers: {
    "Content-Type": "application/json",
  },
});

apiClient.interceptors.response.use(
  (response) => response,
  (error: AxiosError) => {
    if (error.response?.status === 401) {
      // Phase 1.5 will plug in auth store + redirect.
      // For now leave a hook for future logic.
      window.dispatchEvent(new CustomEvent("auth:unauthorized"));
    }
    return Promise.reject(error);
  },
);
