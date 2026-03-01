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
  views?: number;
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
  /** YouTube: private, public, unlisted */
  privacy_status?: "private" | "public" | "unlisted";
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
        const cid = (typeof p.content_id === "string" ? p.content_id.trim() : "").toLowerCase();
        const aid = (typeof p.account_id === "string" ? p.account_id.trim() : "").toLowerCase();
        if (
          !cid ||
          !aid ||
          cid === "undefined" ||
          cid === "null" ||
          aid === "undefined" ||
          aid === "null" ||
          !isValidUuid(cid) ||
          !isValidUuid(aid)
        ) {
          throw new Error("Некорректные данные. Выберите видео и аккаунт заново.");
        }
        const platform = String(p.platform ?? "").trim().toLowerCase();
        const scheduledAt = p.scheduled_at ? String(p.scheduled_at).trim() : "";
        if (!platform || !["youtube", "vk", "tiktok"].includes(platform)) {
          throw new Error("Укажите платформу (YouTube, VK или TikTok).");
        }
        if (!scheduledAt || Number.isNaN(new Date(scheduledAt).getTime())) {
          throw new Error("Укажите дату и время публикации.");
        }
        const privacyStatus = String(p.privacy_status ?? "private").toLowerCase();
        return {
          content_id: cid,
          platform,
          account_id: aid,
          scheduled_at: new Date(scheduledAt).toISOString(),
          title: p.title != null && p.title !== "" ? String(p.title).trim() : undefined,
          description: p.description != null && p.description !== "" ? String(p.description).trim() : undefined,
          privacy_status: privacyStatus,
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
