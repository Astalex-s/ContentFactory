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
    if (pubs.length === 0) {
      throw new Error("Нет публикаций для планирования");
    }
    const invalidStrings = ["undefined", "null", ""];
    for (let i = 0; i < pubs.length; i++) {
      const p = pubs[i];
      const cid = typeof p.content_id === "string" ? p.content_id.trim() : "";
      const aid = typeof p.account_id === "string" ? p.account_id.trim() : "";
      if (invalidStrings.includes(cid) || !isValidUuid(cid)) {
        throw new Error(
          `Публикация ${i + 1}: неверный content_id. Выберите видео заново и обновите страницу.`
        );
      }
      if (invalidStrings.includes(aid) || !isValidUuid(aid)) {
        throw new Error(
          `Публикация ${i + 1}: неверный account_id. Переподключите канал в настройках.`
        );
      }
      if (!p.platform || !p.scheduled_at) {
        throw new Error(`Публикация ${i + 1}: укажите платформу и дату.`);
      }
    }
    const sanitized = {
      publications: pubs.map((p) => {
        const cid = typeof p.content_id === "string" ? p.content_id.trim() : "";
        const aid = typeof p.account_id === "string" ? p.account_id.trim() : "";
        if (!isValidUuid(cid) || !isValidUuid(aid)) {
          throw new Error("Некорректные данные. Обновите страницу.");
        }
        return {
          content_id: cid,
          platform: String(p.platform ?? "").trim(),
          account_id: aid,
          scheduled_at: p.scheduled_at,
          title: p.title != null && p.title !== "" ? String(p.title).trim() : undefined,
          description: p.description != null && p.description !== "" ? String(p.description).trim() : undefined,
        };
      }),
    };
    if (import.meta.env.DEV) {
      console.debug("[publish] Payload:", JSON.stringify(sanitized, null, 2));
    }
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
