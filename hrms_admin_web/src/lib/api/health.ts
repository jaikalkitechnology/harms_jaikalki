import { apiClient } from "./client";

export interface HealthCheck {
  status: string;
  app: string;
  version: string;
  environment: string;
  company: string;
  db: string;
  redis: string;
}

export async function fetchHealth(): Promise<HealthCheck> {
  const { data } = await apiClient.get<HealthCheck>("/health");
  return data;
}
