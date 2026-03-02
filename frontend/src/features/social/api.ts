/**
 * Social accounts and publication API.
 * Uses centralized Axios instance from services/api.
 * baseURL from env (VITE_API_BASE_URL).
 */
import { AxiosError } from "axios";
import { api } from "@/services/api";

export function getErrorMessage(e: unknown): string {
  if (e instanceof AxiosError && e.response?.data) {
    const d = e.response.data as { detail?: string };
    return d.detail ?? e.message;
  }
  return (e as Error).message;
}

export type SocialPlatform = "youtube" | "vk";

const UUID_REGEX =
  /^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/;

function isValidUuid(v: unknown): v is string {
  return typeof v === "string" && v.length > 0 && UUID_REGEX.test(v);
}

export interface SocialAccount {
  id: string;
  platform: string;
  channel_id?: string | null;
  channel_title?: string | null;
  created_at: string | null;
}


export interface ConnectResponse {
  auth_url: string;
}

export interface SchedulePublicationRequest {
  platform: string;
  account_id: string;
  scheduled_at?: string;
  title?: string;
  description?: string;
  /** YouTube: private, public, unlisted */
  privacy_status?: "private" | "public" | "unlisted";
}

export interface SchedulePublicationResponse {
  id: string;
  content_id: string;
  platform: string;
  account_id: string;
  scheduled_at: string;
  status: string;
}

export interface PublicationStatusResponse {
  id: string;
  content_id: string;
  platform: string;
  account_id: string;
  scheduled_at: string | null;
  status: string;
  error_message: string | null;
  platform_video_id: string | null;
  created_at: string | null;
}

export const socialApi = {
  async getConnectUrl(platform: SocialPlatform): Promise<string> {
    const { data } = await api.get<ConnectResponse>(`/social/connect/${platform}`);
    return data.auth_url;
  },

  async getAccounts(): Promise<SocialAccount[]> {
    const { data } = await api.get<{ accounts: SocialAccount[] }>("/social/accounts");
    return (data.accounts ?? []).filter((a) => isValidUuid(a?.id));
  },

  async disconnectAccount(accountId: string): Promise<void> {
    await api.delete(`/social/accounts/${accountId}`);
  },

  async schedulePublication(
    contentId: string,
    body: SchedulePublicationRequest
  ): Promise<SchedulePublicationResponse> {
    const cid = typeof contentId === "string" ? contentId.trim() : "";
    const platform = typeof body.platform === "string" ? body.platform.trim() : "";
    const accountId = typeof body.account_id === "string" ? body.account_id.trim() : "";
    if (!cid || cid === "undefined" || cid === "null" || !isValidUuid(cid)) {
      throw new Error("Некорректный ID контента. Выберите видео заново.");
    }
    if (!platform || !["youtube", "vk"].includes(platform)) {
      throw new Error("Выберите платформу.");
    }
    if (!accountId || accountId === "undefined" || accountId === "null" || !isValidUuid(accountId)) {
      throw new Error("Выберите аккаунт.");
    }
    const payload: Record<string, unknown> = {
      platform,
      account_id: accountId,
      title: body.title != null && body.title !== "" ? String(body.title).trim() : undefined,
      description: body.description != null && body.description !== "" ? String(body.description).trim() : undefined,
      privacy_status: body.privacy_status ?? "private",
    };
    if (body.scheduled_at) payload.scheduled_at = body.scheduled_at;
    const { data } = await api.post<SchedulePublicationResponse>(
      `/publish/${cid}`,
      payload
    );
    return data;
  },

  async getPublicationStatus(
    publicationId: string
  ): Promise<PublicationStatusResponse> {
    const { data } = await api.get<PublicationStatusResponse>(
      `/publish/status/${publicationId}`
    );
    return data;
  },
};
