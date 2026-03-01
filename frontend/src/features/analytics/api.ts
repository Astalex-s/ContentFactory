import { api } from "../../services/api";

export interface ContentMetrics {
  id: string;
  content_id: string;
  platform: string;
  views: number;
  clicks: number;
  ctr: number;
  marketplace_clicks: number;
  recorded_at: string;
}

export interface TopContent {
  content_id: string;
  platform: string;
  views: number;
  clicks: number;
  ctr: number;
}

export interface AggregatedStats {
  total_views: number;
  total_clicks: number;
  avg_ctr: number;
  total_marketplace_clicks: number;
}

export interface ContentRecommendation {
  content_id: string;
  recommendations: string[];
  score: number;
}

export interface PublishTimeRecommendation {
  platform: string;
  recommended_times: string[];
  reasoning: string;
}

export const analyticsApi = {
  getContentMetrics: async (contentId: string): Promise<ContentMetrics[]> => {
    const response = await api.get(`/analytics/metrics/${contentId}`);
    return response.data;
  },

  getTopContent: async (
    limit: number = 10,
    platform?: string
  ): Promise<TopContent[]> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (platform) params.append("platform", platform);
    const response = await api.get(`/analytics/top-content?${params}`);
    return response.data;
  },

  getAggregatedStats: async (platform?: string): Promise<AggregatedStats> => {
    const params = platform ? `?platform=${platform}` : "";
    const response = await api.get(`/analytics/stats${params}`);
    return response.data;
  },

  getContentRecommendations: async (
    contentId: string
  ): Promise<ContentRecommendation> => {
    const response = await api.post(
      `/analytics/recommendations/content/${contentId}`
    );
    return response.data;
  },

  getPublishTimeRecommendations: async (
    platform: string,
    category?: string
  ): Promise<PublishTimeRecommendation> => {
    const params = new URLSearchParams({ platform });
    if (category) params.append("category", category);
    const response = await api.get(
      `/analytics/recommendations/publish-time?${params}`
    );
    return response.data;
  },

  refreshStats: async (
    platform?: string
  ): Promise<{ refreshed: number; failed: number; errors: string[] }> => {
    const params = platform ? `?platform=${platform}` : "";
    const response = await api.post(`/analytics/refresh-stats${params}`);
    return response.data;
  },

  fetchAndRecordStats: async (
    contentId: string,
    platform: string,
    accountId: string,
    videoId: string
  ): Promise<{ success: boolean; metrics: ContentMetrics }> => {
    const params = new URLSearchParams({
      account_id: accountId,
      video_id: videoId,
    });
    const response = await api.post(
      `/analytics/fetch/${contentId}/${platform}?${params}`
    );
    return response.data;
  },
};
