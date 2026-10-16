import { apiClient } from "./client";
import { API_BASE_URL } from "@/lib/constants";

const v1 = "/api/v1";

export interface PayrollRun {
  id: number;
  year: number;
  month: number;
  status: "draft" | "processed" | "finalized" | "reverted";
  run_at: string;
  finalized_at: string | null;
  total_gross: string;
  total_net: string;
  total_employer_cost: string;
  total_employees: number;
  cycle_start_day: number;
  disbursed: boolean;
  disbursed_at: string | null;
}

export interface Payslip {
  id: number;
  payroll_run_id: number;
  employee_id: number;
  year: number;
  month: number;
  basic: string;
  hra: string;
  other_allowance: string;
  gross: string;
  /** Approved incentives paid with this slip (part of gross). */
  incentive?: string;
  pf_employee: string;
  esic_employee: string;
  professional_tax: string;
  tds: string;
  total_deductions: string;
  net_pay: string;
  pf_employer: string;
  esic_employer: string;
  days_paid: string;
  days_lop: string;
  working_days: string;
  days_present: string;
  days_paid_leave: string;
  days_unpaid_leave: string;
  days_absent: string;
  days_holiday: string;
  days_weekoff: string;
  days_sandwich: string;
  is_final_settlement?: boolean;
  on_hold?: boolean;
  pf_wages?: string;
  eps_wages?: string;
  edli_wages?: string;
  pdf_url: string | null;
}

export interface EcrRow {
  employee_id: number;
  employee_code: string;
  uan: string;
  name: string;
  gross_wages: number;
  epf_wages: number;
  eps_wages: number;
  edli_wages: number;
  epf_contri: number;
  eps_contri: number;
  epf_eps_diff: number;
  ncp_days: number;
  refund: number;
  payslip_pf_employee: number;
}

export interface EcrIssue {
  employee_code: string;
  name: string;
  level: "error" | "warning";
  message: string;
}

export interface EcrCheck {
  run_id: number;
  wage_month: string;
  ceilings: { pf: string; eps: string; edli: string };
  rows: EcrRow[];
  excluded: { employee_id: number; employee_code: string; name: string; reason: string }[];
  issues: EcrIssue[];
  errors: number;
  warnings: number;
  ok: boolean;
  totals: {
    members: number;
    epf_wages: number;
    epf_contri: number;
    eps_contri: number;
    epf_eps_diff: number;
  };
}

export interface Reimbursement {
  id: number;
  employee_id: number;
  category: string;
  amount: string;
  bill_date: string;
  description: string | null;
  bill_url: string | null;
  status: "pending" | "approved" | "rejected" | "paid";
  approver_id: number | null;
  approved_at: string | null;
  paid_in_run_id: number | null;
  rejection_reason: string | null;
}

export interface GeneratedDocument {
  id: number;
  employee_id: number;
  doc_type: string;
  letter_number: string | null;
  file_url: string;
  created_at: string;
}

export const payrollApi = {
  async listRuns(): Promise<PayrollRun[]> {
    const { data } = await apiClient.get(`${v1}/payroll/runs`);
    return data;
  },
  async getRun(id: number): Promise<{ run: PayrollRun; payslips: Payslip[] }> {
    const { data } = await apiClient.get(`${v1}/payroll/runs/${id}`);
    return data;
  },
  async runPayroll(
    year: number,
    month: number,
    cycleStartDay?: number | null,
  ): Promise<PayrollRun> {
    const { data } = await apiClient.post(`${v1}/payroll/run`, {
      year,
      month,
      cycle_start_day: cycleStartDay ?? null,
    });
    return data;
  },
  async finalize(id: number): Promise<PayrollRun> {
    const { data } = await apiClient.post(`${v1}/payroll/runs/${id}/finalize`);
    return data;
  },
  async revert(id: number): Promise<PayrollRun> {
    const { data } = await apiClient.post(`${v1}/payroll/runs/${id}/revert`);
    return data;
  },
  async deleteRun(id: number): Promise<void> {
    await apiClient.delete(`${v1}/payroll/runs/${id}`);
  },
  async disburse(id: number): Promise<PayrollRun> {
    const { data } = await apiClient.post(`${v1}/payroll/runs/${id}/disburse`);
    return data;
  },
  async undoDisburse(id: number): Promise<PayrollRun> {
    const { data } = await apiClient.post(
      `${v1}/payroll/runs/${id}/undo-disburse`,
    );
    return data;
  },
  runCsvUrl(id: number): string {
    return `${API_BASE_URL}${v1}/payroll/runs/${id}/export.csv`;
  },
  pfChallanUrl(id: number): string {
    return `${API_BASE_URL}${v1}/payroll/runs/${id}/pf-challan.txt`;
  },
  async checkPfChallan(id: number): Promise<EcrCheck> {
    const { data } = await apiClient.get(
      `${v1}/payroll/runs/${id}/pf-challan/check`,
    );
    return data;
  },
  async pendingReimbursements(): Promise<Reimbursement[]> {
    const { data } = await apiClient.get(
      `${v1}/payroll/reimbursements/pending`,
    );
    return data;
  },
  async listReimbursements(params?: {
    status?: "pending" | "approved" | "rejected" | "paid";
    employee_id?: number;
    category?: string;
    from_date?: string;
    to_date?: string;
    search?: string;
    limit?: number;
    offset?: number;
  }): Promise<Reimbursement[]> {
    const { data } = await apiClient.get(`${v1}/payroll/reimbursements`, {
      params,
    });
    return data;
  },
  async approveReimbursement(id: number): Promise<Reimbursement> {
    const { data } = await apiClient.post(
      `${v1}/payroll/reimbursements/${id}/approve`,
    );
    return data;
  },
  async rejectReimbursement(id: number, reason: string): Promise<Reimbursement> {
    const { data } = await apiClient.post(
      `${v1}/payroll/reimbursements/${id}/reject`,
      { rejection_reason: reason },
    );
    return data;
  },
  async generateOfferLetter(
    employeeId: number,
    onDate?: string,
  ): Promise<GeneratedDocument> {
    const { data } = await apiClient.post(
      `${v1}/payroll/offer-letter/${employeeId}`,
      undefined,
      { params: onDate ? { on_date: onDate } : undefined },
    );
    return data;
  },
  async generateConfirmationLetter(
    employeeId: number,
    onDate?: string,
  ): Promise<GeneratedDocument> {
    const { data } = await apiClient.post(
      `${v1}/payroll/confirmation-letter/${employeeId}`,
      undefined,
      { params: onDate ? { on_date: onDate } : undefined },
    );
    return data;
  },
  async deleteConfirmationLetter(employeeId: number): Promise<void> {
    await apiClient.delete(`${v1}/payroll/confirmation-letter/${employeeId}`);
  },
  async listEmployeeDocuments(
    employeeId: number,
  ): Promise<GeneratedDocument[]> {
    const { data } = await apiClient.get(
      `${v1}/payroll/documents/${employeeId}`,
    );
    return data;
  },
  offerLetterPreviewUrl(employeeId: number, onDate?: string): string {
    const base = `${API_BASE_URL}${v1}/payroll/offer-letter/${employeeId}/preview`;
    return onDate ? `${base}?on_date=${onDate}` : base;
  },
  payslipPdfUrl(payslipId: number): string {
    return `${API_BASE_URL}${v1}/payroll/payslips/${payslipId}/pdf`;
  },
};

// ── PF wage ceiling register + payroll policy ────────────────────────
export type PfMidMonthMode = "day_weighted" | "whole_month" | "next_month";

export interface PfCeiling {
  id: number;
  cap_amount: string;
  eps_cap_amount: string;
  edli_cap_amount: string;
  effective_from: string;
  recorded_on: string;
  mid_month_mode: PfMidMonthMode;
  reference: string | null;
  notes: string | null;
  applies_from: string | null;
  status: "past" | "active" | "scheduled" | null;
  locked: boolean;
}

export interface PfCeilingInput {
  cap_amount: number;
  eps_cap_amount?: number | null;
  edli_cap_amount?: number | null;
  effective_from: string;
  recorded_on?: string | null;
  mid_month_mode: PfMidMonthMode;
  reference?: string | null;
  notes?: string | null;
}

export interface PfCapCurrent {
  pf_cap: string;
  eps_cap: string;
  as_of: string;
  next_change: PfCeiling | null;
}

export interface PfImpactRow {
  employee_id: number;
  employee_code: string;
  name: string;
  basic: number;
  old_pf_employee: number;
  new_pf_employee: number;
  old_pf_employer: number;
  new_pf_employer: number;
  old_gross: number;
  new_gross: number;
  old_net: number;
  new_net: number;
  net_change: number;
  absorb_ctc_annual: number;
}

export interface PfImpact {
  ceiling_id: number;
  old_cap: string;
  new_cap: string;
  first_full_month: string;
  effective_month_cap: string;
  rows: PfImpactRow[];
}

export type DivisionBasis = "calendar_days" | "working_days" | "fixed_30";

export const pfCeilingApi = {
  async list(): Promise<PfCeiling[]> {
    return (await apiClient.get(`${v1}/payroll/pf-ceilings`)).data;
  },
  async current(): Promise<PfCapCurrent> {
    return (await apiClient.get(`${v1}/payroll/pf-ceilings/current`)).data;
  },
  async create(body: PfCeilingInput): Promise<PfCeiling> {
    return (await apiClient.post(`${v1}/payroll/pf-ceilings`, body)).data;
  },
  async update(id: number, body: Partial<PfCeilingInput>): Promise<PfCeiling> {
    return (await apiClient.put(`${v1}/payroll/pf-ceilings/${id}`, body)).data;
  },
  async remove(id: number): Promise<void> {
    await apiClient.delete(`${v1}/payroll/pf-ceilings/${id}`);
  },
  async impact(id: number): Promise<PfImpact> {
    return (await apiClient.get(`${v1}/payroll/pf-ceilings/${id}/impact`)).data;
  },
  async absorb(
    id: number,
    body: { employee_ids: number[]; effective_date?: string; reason?: string },
  ): Promise<{
    created: { employee_id: number; revision_id: number; new_ctc_annual: number }[];
    skipped: { employee_id: number; reason: string }[];
  }> {
    return (await apiClient.post(`${v1}/payroll/pf-ceilings/${id}/absorb`, body)).data;
  },
  async getPolicy(): Promise<{ division_basis: DivisionBasis }> {
    return (await apiClient.get(`${v1}/payroll/policy`)).data;
  },
  async setPolicy(division_basis: DivisionBasis): Promise<{ division_basis: DivisionBasis }> {
    return (await apiClient.put(`${v1}/payroll/policy`, { division_basis })).data;
  },
};
