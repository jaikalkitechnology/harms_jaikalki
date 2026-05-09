import { apiClient } from "./client";

const v1 = "/api/v1";

export type EmployeeDocType =
  // KYC / identity
  | "aadhaar"
  | "pan"
  | "passport"
  | "voter_id"
  | "driving_license"
  | "address_proof"
  | "photo"
  // Banking
  | "bank_passbook"
  | "cancelled_cheque"
  // Education
  | "ssc_marksheet"
  | "hsc_marksheet"
  | "graduation_marksheet"
  | "post_graduation_marksheet"
  | "diploma_certificate"
  | "professional_certificate"
  | "education"
  // Employment history
  | "experience"
  | "prev_offer_letter"
  | "prev_relieving_letter"
  | "prev_payslip"
  | "form16"
  // Internal
  | "offer_letter"
  | "confirmation_letter"
  | "other";

export interface EmployeeDocument {
  id: number;
  employee_id: number;
  doc_type: EmployeeDocType;
  file_name: string;
  file_url: string;
  file_size: number;
  mime_type: string | null;
  verified: boolean;
  expires_at: string | null;
  created_at: string;
}

export const documentsApi = {
  async list(employeeId: number): Promise<EmployeeDocument[]> {
    const { data } = await apiClient.get(
      `${v1}/employees/${employeeId}/documents`,
    );
    return data;
  },
  async upload(
    employeeId: number,
    docType: EmployeeDocType,
    file: File,
  ): Promise<EmployeeDocument> {
    const fd = new FormData();
    fd.append("doc_type", docType);
    fd.append("file", file);
    const { data } = await apiClient.post(
      `${v1}/employees/${employeeId}/documents`,
      fd,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return data;
  },
  async verify(documentId: number): Promise<EmployeeDocument> {
    const { data } = await apiClient.post(
      `${v1}/documents/${documentId}/verify`,
    );
    return data;
  },
  async remove(documentId: number): Promise<void> {
    await apiClient.delete(`${v1}/documents/${documentId}`);
  },
  async signedUrl(documentId: number): Promise<{ url: string }> {
    const { data } = await apiClient.get(
      `${v1}/documents/${documentId}/signed-url`,
    );
    return data;
  },
};
