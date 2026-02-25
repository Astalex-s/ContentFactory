export interface DashboardPipeline {
  imported: number;
  text_generated: number;
  media_generated: number;
  scheduled: number;
  published: number;
  with_analytics: number;
}

export interface DashboardAlerts {
  products_no_content: number;
  publication_failed: number;
  low_ctr_count: number;
  ai_errors_count: number;
}

export interface DashboardStats {
  pipeline: DashboardPipeline;
  alerts: DashboardAlerts;
}

export interface DashboardProduct {
  id: string;
  name: string;
  category: string;
  price: number;
  popularity_score: number;
  content_status: "no_content" | "text_ready" | "image_ready" | "video_ready" | "complete";
  publication_status: "not_scheduled" | "scheduled" | "published" | "failed";
}
