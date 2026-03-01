import axios from "axios";

import { api } from "../../services/api";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

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
    const response = await axios.get(
      `${API_BASE_URL}/analytics/metrics/${contentId}`
    );
    return response.data;
  },

  getTopContent: async (
    limit: number = 10,
    platform?: string
  ): Promise<TopContent[]> => {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (platform) params.append("platform", platform);
    const response = await axios.get(
      `${API_BASE_URL}/analytics/top-content?${params}`
    );
    return response.data;
  },

  getAggregatedStats: async (platform?: string): Promise<AggregatedStats> => {
    const params = platform ? `?platform=${platform}` : "";
    const response = await axios.get(
      `${API_BASE_URL}/analytics/stats${params}`
    );
    return response.data;
  },

  getContentRecommendations: async (
    contentId: string
  ): Promise<ContentRecommendation> => {
    const response = await axios.post(
      `${API_BASE_URL}/analytics/recommendations/content/${contentId}`
    );
    return response.data;
  },

  getPublishTimeRecommendations: async (
    platform: string,
    category?: string
  ): Promise<PublishTimeRecommendation> => {
    const params = new URLSearchParams({ platform });
    if (category) params.append("category", category);
    const response = await axios.get(
      `${API_BASE_URL}/analytics/recommendations/publish-time?${params}`
    );
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
