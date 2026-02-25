import { api } from "./api";

export interface GeneratedContent {
  id: string;
  product_id: string;
  content_type: "text" | "image" | "video";
  content_text?: string;
  file_path?: string;
  platform: string;
  status: "draft" | "ready" | "published";
  created_at: string;
}

export interface ContentListResponse {
  items: GeneratedContent[];
  total: number;
  page: number;
  page_size: number;
}

export const contentService = {
  async getAllContent(page = 1, pageSize = 20): Promise<ContentListResponse> {
    const response = await api.get<ContentListResponse>("/content/all", {
      params: { page, page_size: pageSize },
    });
    return response.data;
  },

  async getContentByProduct(
    productId: string,
    page = 1,
    pageSize = 20
  ): Promise<ContentListResponse> {
    const response = await api.get<ContentListResponse>(
      `/content/product/${productId}`,
      {
        params: { page, page_size: pageSize },
      }
    );
    return response.data;
  },
};
