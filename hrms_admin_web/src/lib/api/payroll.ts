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
  pdf_url: string | null;
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
  async runPayroll(year: number, month: number): Promise<PayrollRun> {
    const { data } = await apiClient.post(`${v1}/payroll/run`, {
      year,
      month,
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
  async generateOfferLetter(employeeId: number): Promise<GeneratedDocument> {
    const { data } = await apiClient.post(
      `${v1}/payroll/offer-letter/${employeeId}`,
    );
    return data;
  },
  async generateConfirmationLetter(
    employeeId: number,
  ): Promise<GeneratedDocument> {
    const { data } = await apiClient.post(
      `${v1}/payroll/confirmation-letter/${employeeId}`,
    );
    return data;
  },
  async listEmployeeDocuments(
    employeeId: number,
  ): Promise<GeneratedDocument[]> {
    const { data } = await apiClient.get(
      `${v1}/payroll/documents/${employeeId}`,
    );
    return data;
  },
  offerLetterPreviewUrl(employeeId: number): string {
    return `${API_BASE_URL}${v1}/payroll/offer-letter/${employeeId}/preview`;
  },
  payslipPdfUrl(payslipId: number): string {
    return `${API_BASE_URL}${v1}/payroll/payslips/${payslipId}/pdf`;
  },
};
