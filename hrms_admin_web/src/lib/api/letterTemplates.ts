import { apiClient } from "./client";
import { API_BASE_URL } from "@/lib/constants";

const V1 = "/api/v1";

export interface LetterTemplate {
  id: number;
  code: string;
  name: string;
  category: string;
  subject: string | null;
  body: string;
  is_active: boolean;
  placeholders: string | null;
  created_at: string;
  updated_at: string | null;
}

export interface LetterPlaceholderHint {
  key: string;
  description: string;
}

export interface LetterTemplateCreate {
  code: string;
  name: string;
  category: string;
  subject?: string | null;
  body: string;
  is_active?: boolean;
  placeholders?: string | null;
}

export type LetterTemplateUpdate = Partial<
  Omit<LetterTemplateCreate, "code">
>;

export interface LetterGenerateOptions {
  letter_no?: string;
  on_date?: string;
  last_working_date?: string;
  ctc_amount?: string;
  ctc_amount_words?: string;
  overrides?: Record<string, string>;
}

export const letterTemplatesApi = {
  list: async (includeInactive = true): Promise<LetterTemplate[]> =>
    (
      await apiClient.get(`${V1}/letter-templates`, {
        params: { include_inactive: includeInactive },
      })
    ).data,
  placeholders: async (): Promise<LetterPlaceholderHint[]> =>
    (await apiClient.get(`${V1}/letter-templates/placeholders`)).data,
  create: async (body: LetterTemplateCreate): Promise<LetterTemplate> =>
    (await apiClient.post(`${V1}/letter-templates`, body)).data,
  update: async (
    id: number,
    body: LetterTemplateUpdate,
  ): Promise<LetterTemplate> =>
    (await apiClient.put(`${V1}/letter-templates/${id}`, body)).data,
  remove: async (id: number): Promise<void> =>
    (await apiClient.delete(`${V1}/letter-templates/${id}`)).data,

  generateUrl: (employeeId: number, templateId: number): string =>
    `${API_BASE_URL}${V1}/employees/${employeeId}/letters/${templateId}/generate`,

  generate: async (
    employeeId: number,
    templateId: number,
    options: LetterGenerateOptions = {},
  ): Promise<Blob> => {
    const res = await apiClient.post(
      `${V1}/employees/${employeeId}/letters/${templateId}/generate`,
      options,
      { responseType: "blob" },
    );
    return res.data as Blob;
  },
};
