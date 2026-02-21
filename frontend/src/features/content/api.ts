/**
 * Content generation API.
 * Uses centralized Axios instance from services/api.
 */
import { api } from "@/services/api";

export type Platform = "youtube" | "vk" | "rutube";
export type Tone = "neutral" | "emotional" | "expert";

export interface GeneratedVariant {
  id: string;
  text: string;
  variant: number;
}

export interface GenerateContentResponse {
  product_id: string;
  generated_variants: GeneratedVariant[];
}

export interface GenerateContentRequest {
  platform: Platform;
  tone: Tone;
}

/** Timeout for content generation (3 AI calls ~15–20 sec) */
const GENERATE_TIMEOUT_MS = 60000;

export const contentApi = {
  async generate(
    productId: string,
    body: GenerateContentRequest
  ): Promise<GenerateContentResponse> {
    const { data } = await api.post<GenerateContentResponse>(
      `/content/generate/${productId}`,
      body,
      { timeout: GENERATE_TIMEOUT_MS }
    );
    return data;
  },
};
