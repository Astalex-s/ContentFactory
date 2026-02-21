/**
 * Content generation API.
 * Uses centralized Axios instance from services/api.
 */
import { api } from "@/services/api";

export type Platform = "youtube" | "vk" | "rutube";
export type Tone = "neutral" | "emotional" | "expert";
export type ContentTextType =
  | "short_post"
  | "video_description"
  | "cta"
  | "all";

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
  content_text_type?: ContentTextType;
}

export interface GeneratedContentItem {
  id: string;
  product_id: string;
  content_type: string;
  content_text_type: string;
  content_text: string | null;
  file_path: string | null;
  status: string;
  content_variant: number;
  platform: string;
  tone: string;
  ai_model: string | null;
  created_at: string;
}

export interface ContentListResponse {
  items: GeneratedContentItem[];
  total: number;
  page: number;
  page_size: number;
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

  async getContentByProduct(
    productId: string,
    page = 1,
    pageSize = 20
  ): Promise<ContentListResponse> {
    const { data } = await api.get<ContentListResponse>(
      `/content/product/${productId}`,
      { params: { page, page_size: pageSize } }
    );
    return data;
  },

  async hasContent(productId: string): Promise<boolean> {
    const { data } = await api.get<{ has_content: boolean }>(
      `/content/product/${productId}/has`
    );
    return data.has_content;
  },

  async updateContent(
    contentId: string,
    contentText: string
  ): Promise<GeneratedContentItem> {
    const { data } = await api.patch<GeneratedContentItem>(
      `/content/${contentId}`,
      { content_text: contentText }
    );
    return data;
  },

  async deleteContent(contentId: string): Promise<void> {
    await api.delete(`/content/${contentId}`);
  },
};
