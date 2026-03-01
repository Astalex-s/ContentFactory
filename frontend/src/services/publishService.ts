import axios from "axios";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

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
    const response = await axios.get(`${API_BASE_URL}/publish/`, { params });
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
    const response = await axios.post(
      `${API_BASE_URL}/publish/${contentId}`,
      data
    );
    return response.data;
  },

  async bulkSchedulePublications(
    data: BulkPublishRequest
  ): Promise<BulkPublishResponse> {
    const response = await axios.post(`${API_BASE_URL}/publish/bulk`, data);
    return response.data;
  },

  async getPublicationStatus(id: string): Promise<{
    id: string;
    status: string;
    error_message?: string;
    platform_video_id?: string;
  }> {
    const response = await axios.get(`${API_BASE_URL}/publish/status/${id}`);
    return response.data;
  },

  async cancelPublication(id: string): Promise<{ message: string }> {
    const response = await axios.delete(`${API_BASE_URL}/publish/${id}`);
    return response.data;
  },
};
