import { apiClient } from "./client";

export interface Category {
  id: number;
  code: string;
  name: string;
  description: string | null;
  has_salary: boolean;
  only_travel_expense: boolean;
  requires_probation: boolean;
  default_probation_months: number;
}

export interface Department {
  id: number;
  code: string;
  name: string;
  description: string | null;
}

export interface Designation {
  id: number;
  code: string;
  name: string;
  level: number;
  department_id: number | null;
}

export interface SalaryTemplate {
  id: number;
  template_code: string;
  template_name: string;
  category: "intern" | "trainee" | "permanent" | "contract";
  designation_level: number;
  ctc_annual_default: string;
  basic_amount: string;
  hra_amount: string;
  other_allowance: string;
  travel_expense_max: string;
  has_probation: boolean;
  probation_months: number;
  is_active: boolean;
}

export interface SalaryBreakup {
  template_code: string;
  template_name: string;
  category: string;
  is_intern: boolean;
  basic: number;
  hra: number;
  other_allowance: number;
  special_allowance: number;
  conveyance: number;
  medical_allowance: number;
  lta: number;
  food_coupon: number;
  gross: number;
  pf_employee: number;
  esic_employee: number;
  professional_tax: number;
  total_deductions: number;
  net_salary: number;
  pf_employer: number;
  esic_employer: number;
  total_ctc_monthly: number;
  total_ctc_annual: number;
  travel_expense_max: number;
  is_paid_internship: boolean;
  notes: string[];
}

export interface EmployeeListItem {
  id: number;
  employee_code: string;
  first_name: string;
  last_name: string;
  photo_url: string | null;
  designation: Designation | null;
  department: Department | null;
  category: Category | null;
  is_on_probation: boolean;
  status: string;
  date_of_joining: string | null;
}

export interface EmployeeDetail extends EmployeeListItem {
  user_id: number | null;
  date_of_birth: string | null;
  blood_group: string | null;
  gender: string | null;
  marital_status: string | null;
  personal_email: string | null;
  personal_phone: string | null;
  reporting_to: number | null;
  probation_end_date: string | null;
  confirmation_date: string | null;
  exit_date: string | null;
  salary_template: SalaryTemplate | null;
  ctc_annual: string;
  work_location: string;
  employment_type: string;
  work_mode: string;
}

export interface ExpiringProbation {
  employee_id: number;
  employee_code: string;
  full_name: string;
  probation_end_date: string;
  days_remaining: number;
}

export interface CreateEmployeePayload {
  first_name: string;
  last_name: string;
  category_id: number;
  designation_id?: number | null;
  department_id?: number | null;
  reporting_to?: number | null;
  salary_template_id?: number | null;
  ctc_annual?: number | null;
  date_of_joining: string;
  personal_email?: string | null;
  personal_phone?: string | null;
  work_location?: string | null;
  employment_type?: string;
  work_mode?: string;
  create_user_account?: boolean;
  user_email?: string | null;
}

const v1 = "/api/v1";

export const employeesApi = {
  async list(params: {
    search?: string;
    department_id?: number;
    category_id?: number;
    on_probation?: boolean;
  } = {}): Promise<EmployeeListItem[]> {
    const { data } = await apiClient.get(`${v1}/employees`, { params });
    return data;
  },

  async get(id: number): Promise<EmployeeDetail> {
    const { data } = await apiClient.get(`${v1}/employees/${id}`);
    return data;
  },

  async create(payload: CreateEmployeePayload): Promise<EmployeeDetail> {
    const { data } = await apiClient.post(`${v1}/employees`, payload);
    return data;
  },

  async update(id: number, payload: Partial<EmployeeDetail>): Promise<EmployeeDetail> {
    const { data } = await apiClient.put(`${v1}/employees/${id}`, payload);
    return data;
  },

  async expiringProbations(days = 30): Promise<ExpiringProbation[]> {
    const { data } = await apiClient.get(
      `${v1}/employees/probation/expiring`,
      { params: { days } },
    );
    return data;
  },

  async confirm(id: number, letterUrl?: string | null): Promise<unknown> {
    const { data } = await apiClient.post(`${v1}/employees/${id}/confirm`, {
      confirmation_letter_url: letterUrl ?? null,
    });
    return data;
  },

  async extendProbation(
    id: number,
    months: number,
    reason: string,
  ): Promise<unknown> {
    const { data } = await apiClient.post(
      `${v1}/employees/${id}/extend-probation`,
      { months, reason },
    );
    return data;
  },

  async orgChart(): Promise<unknown[]> {
    const { data } = await apiClient.get(`${v1}/employees/org/chart`);
    return data;
  },
};

export const lookupsApi = {
  async categories(): Promise<Category[]> {
    const { data } = await apiClient.get(`${v1}/employee-categories`);
    return data;
  },
  async departments(): Promise<Department[]> {
    const { data } = await apiClient.get(`${v1}/departments`);
    return data;
  },
  async designations(): Promise<Designation[]> {
    const { data } = await apiClient.get(`${v1}/designations`);
    return data;
  },
};

export const salaryTemplatesApi = {
  async list(category?: string): Promise<SalaryTemplate[]> {
    const { data } = await apiClient.get(`${v1}/salary-templates`, {
      params: category ? { category } : undefined,
    });
    return data;
  },

  async calculate(id: number, ctc?: number): Promise<SalaryBreakup> {
    const { data } = await apiClient.get(
      `${v1}/salary-templates/${id}/calculate`,
      { params: ctc ? { ctc } : undefined },
    );
    return data;
  },
};

export interface InternExpense {
  id: number;
  employee_id: number;
  expense_date: string;
  expense_type: string;
  amount: string;
  receipt_url: string | null;
  description: string | null;
  status: "pending" | "approved" | "rejected" | "reimbursed";
  approved_by: number | null;
  approved_at: string | null;
  reimbursed_at: string | null;
  rejection_reason: string | null;
  created_at: string;
}

export const internExpensesApi = {
  async pending(): Promise<InternExpense[]> {
    const { data } = await apiClient.get(`${v1}/interns/expenses/pending`);
    return data;
  },
  async report(): Promise<InternExpense[]> {
    const { data } = await apiClient.get(`${v1}/interns/expenses/report`);
    return data;
  },
  async approve(id: number): Promise<InternExpense> {
    const { data } = await apiClient.post(`${v1}/interns/expenses/${id}/approve`);
    return data;
  },
  async reject(id: number, reason: string): Promise<InternExpense> {
    const { data } = await apiClient.post(
      `${v1}/interns/expenses/${id}/reject`,
      { rejection_reason: reason },
    );
    return data;
  },
  async reimburse(id: number): Promise<InternExpense> {
    const { data } = await apiClient.post(
      `${v1}/interns/expenses/${id}/reimburse`,
    );
    return data;
  },
};
