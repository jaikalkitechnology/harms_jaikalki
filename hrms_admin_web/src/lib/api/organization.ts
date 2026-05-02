import { apiClient } from "./client";

const v1 = "/api/v1";

export interface Department {
  id: number;
  code: string;
  name: string;
  description: string | null;
  head_id: number | null;
}

export interface Designation {
  id: number;
  code: string;
  name: string;
  level: number;
  department_id: number | null;
}

export interface Shift {
  id: number;
  code: string;
  name: string;
  start_time: string; // "HH:MM:SS"
  end_time: string;
  break_duration_min: number;
  is_default: boolean;
  is_active: boolean;
}

export const organizationApi = {
  // Departments
  listDepartments: async (): Promise<Department[]> =>
    (await apiClient.get(`${v1}/departments`)).data,
  createDepartment: async (body: {
    code: string;
    name: string;
    description?: string;
  }): Promise<Department> =>
    (await apiClient.post(`${v1}/departments`, body)).data,
  updateDepartment: async (
    id: number,
    body: { name?: string; description?: string; head_id?: number | null },
  ): Promise<Department> =>
    (await apiClient.put(`${v1}/departments/${id}`, body)).data,
  deleteDepartment: async (id: number): Promise<void> => {
    await apiClient.delete(`${v1}/departments/${id}`);
  },

  // Designations
  listDesignations: async (): Promise<Designation[]> =>
    (await apiClient.get(`${v1}/designations`)).data,
  createDesignation: async (body: {
    code: string;
    name: string;
    level: number;
    department_id?: number | null;
  }): Promise<Designation> =>
    (await apiClient.post(`${v1}/designations`, body)).data,
  updateDesignation: async (
    id: number,
    body: {
      name?: string;
      level?: number;
      department_id?: number | null;
    },
  ): Promise<Designation> =>
    (await apiClient.put(`${v1}/designations/${id}`, body)).data,
  deleteDesignation: async (id: number): Promise<void> => {
    await apiClient.delete(`${v1}/designations/${id}`);
  },

  // Shifts
  listShifts: async (): Promise<Shift[]> =>
    (await apiClient.get(`${v1}/shifts`)).data,
  createShift: async (body: {
    code: string;
    name: string;
    start_time: string;
    end_time: string;
    break_duration_min: number;
    is_default: boolean;
    is_active: boolean;
  }): Promise<Shift> => (await apiClient.post(`${v1}/shifts`, body)).data,
  updateShift: async (
    id: number,
    body: Partial<Omit<Shift, "id" | "code">>,
  ): Promise<Shift> => (await apiClient.put(`${v1}/shifts/${id}`, body)).data,
  deleteShift: async (id: number): Promise<void> => {
    await apiClient.delete(`${v1}/shifts/${id}`);
  },
};
