export const APP_NAME = import.meta.env.VITE_APP_NAME ?? "Jaikalki HRMS";
export const COMPANY_NAME =
  import.meta.env.VITE_COMPANY_NAME ?? "Jaikalki Technology Pvt Ltd";
export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export const ROLES = [
  "super_admin",
  "admin",
  "director",
  "hr",
  "manager",
  "employee",
  "field",
  "trainer",
  "intern",
] as const;
export type Role = (typeof ROLES)[number];

export const ROLE_LABEL: Record<Role, string> = {
  super_admin: "Super Admin",
  admin: "Admin",
  director: "Director",
  hr: "HR",
  manager: "Manager",
  employee: "Employee",
  field: "Field Force",
  trainer: "Trainer",
  intern: "Intern",
};

export const ROLE_COLOR: Record<Role, string> = {
  super_admin: "bg-role-superadmin",
  admin: "bg-role-admin",
  director: "bg-role-director",
  hr: "bg-role-hr",
  manager: "bg-role-manager",
  employee: "bg-role-employee",
  field: "bg-role-field",
  trainer: "bg-role-trainer",
  intern: "bg-role-intern",
};
