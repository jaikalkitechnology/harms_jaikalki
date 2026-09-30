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
  basic_percentage: string;
  hra_amount: string;
  hra_percentage: string;
  other_allowance: string;
  special_allowance: string;
  conveyance: string;
  medical_allowance: string;
  lta: string;
  food_coupon: string;
  travel_expense_max: string;
  is_paid_internship: boolean;
  has_probation: boolean;
  probation_months: number;
  probation_extension_months: number;
  mediclaim_amount: string;
  pa_insurance_amount: string;
  notice_period_probation: number;
  notice_period_confirmed: number;
  notice_period_termination: number;
  is_active: boolean;
}

export type SalaryTemplateInput = Omit<SalaryTemplate, "id">;

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
  exit_date?: string | null;
}

export interface CompletenessItem {
  key: string;
  label: string;
  /** Profile tab that fixes it. */
  section: string;
  done: boolean;
}

export interface Completeness {
  employee_id: number;
  done: number;
  total: number;
  percent: number;
  missing: CompletenessItem[];
  items: CompletenessItem[];
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
  resignation_unlocked: boolean;
  pf_opt_out: boolean;
  eps_member?: boolean;
  pf_basic_cap_override: string | null;
  esic_force_exempt: boolean;
  pt_state: string | null;
  pf_number: string | null;
  uan_number: string | null;
  esic_number: string | null;
  insurance_company: string | null;
  insurance_policy_no: string | null;
  attendance_cycle_start_day: number;
  backdate_from: string | null;
  backdate_to: string | null;
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
    limit?: number;
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

  async getCredential(id: number): Promise<{
    user_id: number;
    email: string;
    is_active: boolean;
    has_account: boolean;
  }> {
    const { data } = await apiClient.get(`${v1}/employees/${id}/credential`);
    return data;
  },
  async createCredential(
    id: number,
    payload: { email: string; password: string; role_code?: string },
  ) {
    const { data } = await apiClient.post(
      `${v1}/employees/${id}/credential`,
      payload,
    );
    return data;
  },
  async resetCredentialPassword(id: number, newPassword: string) {
    const { data } = await apiClient.post(
      `${v1}/employees/${id}/credential/password`,
      { new_password: newPassword },
    );
    return data;
  },
  async setCredentialActive(id: number, isActive: boolean) {
    const { data } = await apiClient.post(
      `${v1}/employees/${id}/credential/active`,
      { is_active: isActive },
    );
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

  async completeness(id: number): Promise<Completeness> {
    const { data } = await apiClient.get(`${v1}/employees/${id}/completeness`);
    return data;
  },

  async completenessAll(): Promise<Record<string, Completeness>> {
    const { data } = await apiClient.get(`${v1}/employees/completeness`);
    return data;
  },

  async orgChart(): Promise<unknown[]> {
    const { data } = await apiClient.get(`${v1}/employees/org/chart`);
    return data;
  },
};

// ── Onboarding lifecycle ──────────────────────────────────────────────
export interface LifecyclePhase {
  id: number;
  employee_id: number;
  phase: "intern" | "probation";
  probation_start_date: string;
  probation_end_date: string;
  is_extended: boolean;
  extension_end_date: string | null;
  extension_reason: string | null;
  status: "in_progress" | "extended" | "confirmed" | "terminated";
  confirmed_date: string | null;
  confirmed_by: number | null;
}

export interface LifecycleState {
  employee_id: number;
  stage: "intern" | "probation" | "confirmed";
  is_on_probation: boolean;
  confirmation_date: string | null;
  history: LifecyclePhase[];
}

export const lifecycleApi = {
  async get(employeeId: number): Promise<LifecycleState> {
    const { data } = await apiClient.get<LifecycleState>(
      `${v1}/employees/${employeeId}/lifecycle`,
    );
    return data;
  },
  async startIntern(
    employeeId: number,
    body: { start_date: string; months?: number },
  ): Promise<LifecyclePhase> {
    const { data } = await apiClient.post<LifecyclePhase>(
      `${v1}/employees/${employeeId}/lifecycle/intern/start`,
      body,
    );
    return data;
  },
  async extendIntern(
    employeeId: number,
    body: { extension_end_date: string; reason?: string },
  ): Promise<LifecyclePhase> {
    const { data } = await apiClient.post<LifecyclePhase>(
      `${v1}/employees/${employeeId}/lifecycle/intern/extend`,
      body,
    );
    return data;
  },
  async startProbation(
    employeeId: number,
    body: { start_date: string; months?: number },
  ): Promise<LifecyclePhase> {
    const { data } = await apiClient.post<LifecyclePhase>(
      `${v1}/employees/${employeeId}/lifecycle/probation/start`,
      body,
    );
    return data;
  },
  async extendProbation(
    employeeId: number,
    body: { extension_end_date: string; reason?: string },
  ): Promise<LifecyclePhase> {
    const { data } = await apiClient.post<LifecyclePhase>(
      `${v1}/employees/${employeeId}/lifecycle/probation/extend`,
      body,
    );
    return data;
  },
  async confirm(
    employeeId: number,
    body: { confirmed_on?: string } = {},
  ): Promise<LifecyclePhase> {
    const { data } = await apiClient.post<LifecyclePhase>(
      `${v1}/employees/${employeeId}/lifecycle/confirm`,
      body,
    );
    return data;
  },
  async undo(
    employeeId: number,
  ): Promise<{ action: string; phase: string | null; id: number | null }> {
    const { data } = await apiClient.post<{
      action: string;
      phase: string | null;
      id: number | null;
    }>(`${v1}/employees/${employeeId}/lifecycle/undo`);
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
  async list(
    category?: string,
    activeOnly = false,
  ): Promise<SalaryTemplate[]> {
    const params: Record<string, unknown> = { active_only: activeOnly };
    if (category) params.category = category;
    const { data } = await apiClient.get(`${v1}/salary-templates`, { params });
    return data;
  },

  async calculate(
    id: number,
    ctc?: number,
    employee_id?: number,
  ): Promise<SalaryBreakup> {
    const params: Record<string, number> = {};
    if (ctc) params.ctc = ctc;
    if (employee_id) params.employee_id = employee_id;
    const { data } = await apiClient.get(
      `${v1}/salary-templates/${id}/calculate`,
      { params: Object.keys(params).length ? params : undefined },
    );
    return data;
  },

  async create(body: SalaryTemplateInput): Promise<SalaryTemplate> {
    const { data } = await apiClient.post(`${v1}/salary-templates`, body);
    return data;
  },

  async update(
    id: number,
    body: Partial<SalaryTemplateInput>,
  ): Promise<SalaryTemplate> {
    const { data } = await apiClient.put(
      `${v1}/salary-templates/${id}`,
      body,
    );
    return data;
  },

  async remove(id: number): Promise<void> {
    await apiClient.delete(`${v1}/salary-templates/${id}`);
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
