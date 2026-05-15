import { apiClient } from "./client";

const v1 = "/api/v1";

// ── Passport / visa ────────────────────────────────────────────────
export interface PassportRecord {
  id: number;
  employee_id: number;
  passport_no: string;
  passport_country: string;
  passport_issue_date: string | null;
  passport_expiry_date: string | null;
  passport_place_of_issue: string | null;
  visa_no: string | null;
  visa_type: string | null;
  visa_country: string | null;
  visa_issue_date: string | null;
  visa_expiry_date: string | null;
  created_at: string;
}

export type PassportInput = Omit<PassportRecord, "id" | "employee_id" | "created_at">;

// ── Nominees ───────────────────────────────────────────────────────
export type NomineeType = "pf" | "gratuity" | "insurance" | "general";

export interface Nominee {
  id: number;
  employee_id: number;
  name: string;
  relation: string;
  date_of_birth: string | null;
  share_pct: string;
  nominee_type: NomineeType;
  address: string | null;
  phone: string | null;
  id_proof_url: string | null;
  is_minor: boolean;
  guardian_name: string | null;
}

export type NomineeInput = Omit<Nominee, "id" | "employee_id">;

// ── Family ─────────────────────────────────────────────────────────
export interface FamilyMember {
  id: number;
  employee_id: number;
  name: string;
  relation: string;
  dob: string | null;
  is_dependent: boolean;
}

export type FamilyMemberInput = Omit<FamilyMember, "id" | "employee_id">;

// ── Bank account ───────────────────────────────────────────────────
export interface BankDetails {
  id: number;
  employee_id: number;
  account_no: string;
  ifsc: string;
  bank_name: string;
  branch: string | null;
  account_holder_name: string | null;
}

export type BankDetailsInput = Omit<BankDetails, "id" | "employee_id">;

export const bankApi = {
  async get(employeeId: number): Promise<BankDetails | null> {
    const { data } = await apiClient.get(`${v1}/employees/${employeeId}/bank`);
    return data;
  },
  async upsert(
    employeeId: number,
    payload: BankDetailsInput,
  ): Promise<BankDetails> {
    const { data } = await apiClient.put(
      `${v1}/employees/${employeeId}/bank`,
      payload,
    );
    return data;
  },
  async remove(employeeId: number): Promise<void> {
    await apiClient.delete(`${v1}/employees/${employeeId}/bank`);
  },
};

// ── Attendance cycles ──────────────────────────────────────────────
export interface AttendanceCycle {
  id: number;
  code: string;
  name: string;
  start_day: number;
  description: string | null;
  is_default: boolean;
  is_active: boolean;
}

export type AttendanceCycleInput = Omit<AttendanceCycle, "id">;

export const attendanceCyclesApi = {
  async list(activeOnly = true): Promise<AttendanceCycle[]> {
    const { data } = await apiClient.get(`${v1}/attendance-cycles`, {
      params: { active_only: activeOnly },
    });
    return data;
  },
  async create(payload: AttendanceCycleInput): Promise<AttendanceCycle> {
    const { data } = await apiClient.post(`${v1}/attendance-cycles`, payload);
    return data;
  },
  async update(
    id: number,
    payload: Partial<AttendanceCycleInput>,
  ): Promise<AttendanceCycle> {
    const { data } = await apiClient.put(
      `${v1}/attendance-cycles/${id}`,
      payload,
    );
    return data;
  },
  async remove(id: number): Promise<void> {
    await apiClient.delete(`${v1}/attendance-cycles/${id}`);
  },
};

export const employeeProfileApi = {
  // photo
  async uploadPhoto(employeeId: number, file: File): Promise<{ photo_url: string }> {
    const fd = new FormData();
    fd.append("file", file);
    const { data } = await apiClient.post(
      `${v1}/employees/${employeeId}/photo`,
      fd,
      { headers: { "Content-Type": "multipart/form-data" } },
    );
    return data;
  },

  // passport
  async getPassport(employeeId: number): Promise<PassportRecord | null> {
    const { data } = await apiClient.get(
      `${v1}/employees/${employeeId}/passport`,
    );
    return data;
  },
  async upsertPassport(
    employeeId: number,
    payload: PassportInput,
  ): Promise<PassportRecord> {
    const { data } = await apiClient.put(
      `${v1}/employees/${employeeId}/passport`,
      payload,
    );
    return data;
  },
  async deletePassport(employeeId: number): Promise<void> {
    await apiClient.delete(`${v1}/employees/${employeeId}/passport`);
  },

  // nominees
  async listNominees(employeeId: number): Promise<Nominee[]> {
    const { data } = await apiClient.get(
      `${v1}/employees/${employeeId}/nominees`,
    );
    return data;
  },
  async createNominee(
    employeeId: number,
    payload: NomineeInput,
  ): Promise<Nominee> {
    const { data } = await apiClient.post(
      `${v1}/employees/${employeeId}/nominees`,
      payload,
    );
    return data;
  },
  async updateNominee(
    nomineeId: number,
    payload: Partial<NomineeInput>,
  ): Promise<Nominee> {
    const { data } = await apiClient.put(
      `${v1}/nominees/${nomineeId}`,
      payload,
    );
    return data;
  },
  async deleteNominee(nomineeId: number): Promise<void> {
    await apiClient.delete(`${v1}/nominees/${nomineeId}`);
  },

  // family
  async listFamily(employeeId: number): Promise<FamilyMember[]> {
    const { data } = await apiClient.get(
      `${v1}/employees/${employeeId}/family`,
    );
    return data;
  },
  async createFamily(
    employeeId: number,
    payload: FamilyMemberInput,
  ): Promise<FamilyMember> {
    const { data } = await apiClient.post(
      `${v1}/employees/${employeeId}/family`,
      payload,
    );
    return data;
  },
  async updateFamily(
    memberId: number,
    payload: Partial<FamilyMemberInput>,
  ): Promise<FamilyMember> {
    const { data } = await apiClient.put(
      `${v1}/family/${memberId}`,
      payload,
    );
    return data;
  },
  async deleteFamily(memberId: number): Promise<void> {
    await apiClient.delete(`${v1}/family/${memberId}`);
  },
};
