import { api } from "./api";

const UUID_REGEX =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

function isValidUuid(v: unknown): v is string {
  return typeof v === "string" && v.length > 0 && UUID_REGEX.test(v);
}

export interface PublicationItem {
  id: string;
  content_id: string;
  platform: string;
  account_id: string;
  scheduled_at: string;
  status: "pending" | "processing" | "published" | "failed";
  error_message?: string;
  platform_video_id?: string;
  created_at: string;
  content_file_path?: string;
  content_type?: string;
}

export interface PublicationListResponse {
  total: number;
  items: PublicationItem[];
  limit: number;
  offset: number;
}

export interface PublicationScheduleItem {
  content_id: string;
  platform: string;
  account_id: string;
  scheduled_at: string;
  title?: string;
  description?: string;
}

export interface BulkPublishRequest {
  publications: PublicationScheduleItem[];
}

export interface BulkPublishResponse {
  created_count: number;
  publications: PublicationItem[];
}

export const publishService = {
  async getPublications(params?: {
    status?: string;
    platform?: string;
    limit?: number;
    offset?: number;
  }): Promise<PublicationListResponse> {
    const response = await api.get<PublicationListResponse>("/publish/", {
      params,
    });
    return response.data;
  },

  async schedulePublication(
    contentId: string,
    data: {
      platform: string;
      account_id: string;
      scheduled_at?: string;
      title?: string;
      description?: string;
    }
  ): Promise<PublicationItem> {
    const response = await api.post<PublicationItem>(
      `/publish/${contentId}`,
      data
    );
    return response.data;
  },

  async bulkSchedulePublications(
    data: BulkPublishRequest
  ): Promise<BulkPublishResponse> {
    const pubs = data.publications ?? [];
    for (let i = 0; i < pubs.length; i++) {
      const p = pubs[i];
      if (!isValidUuid(p.content_id)) {
        throw new Error(
          `Публикация ${i + 1}: неверный content_id (ожидается UUID). Обновите страницу.`
        );
      }
      if (!isValidUuid(p.account_id)) {
        throw new Error(
          `Публикация ${i + 1}: неверный account_id (ожидается UUID). Переподключите канал.`
        );
      }
    }
    const sanitized = {
      publications: pubs.map((p) => ({
        content_id: p.content_id,
        platform: p.platform,
        account_id: p.account_id,
        scheduled_at: p.scheduled_at,
        title: p.title ?? undefined,
        description: p.description ?? undefined,
      })),
    };
    const response = await api.post<BulkPublishResponse>(
      "/publish/bulk",
      sanitized
    );
    return response.data;
  },

  async getPublicationStatus(id: string): Promise<{
    id: string;
    status: string;
    error_message?: string;
    platform_video_id?: string;
  }> {
    const response = await api.get<{
      id: string;
      status: string;
      error_message?: string;
      platform_video_id?: string;
    }>(`/publish/status/${id}`);
    return response.data;
  },

  async cancelPublication(id: string): Promise<{ message: string }> {
    const response = await api.delete<{ message: string }>(`/publish/${id}`);
    return response.data;
  },
};
