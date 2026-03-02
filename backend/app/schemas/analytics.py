"""Analytics schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class RecordMetricsRequest(BaseModel):
    """Request to record metrics."""

    content_id: UUID
    platform: str
    views: int = Field(ge=0)
    clicks: int = Field(ge=0)
    marketplace_clicks: int = Field(default=0, ge=0)
    recorded_at: datetime | None = None


class ContentMetricsResponse(BaseModel):
    """Content metrics response."""

    id: str
    content_id: str
    platform: str
    views: int
    clicks: int
    ctr: float
    marketplace_clicks: int
    recorded_at: str


class TopContentResponse(BaseModel):
    """Top content response."""

    content_id: str
    platform: str
    views: int
    clicks: int
    ctr: float
    content_file_path: str | None = None
    content_type: str | None = None
    platform_video_id: str | None = None


class AggregatedStatsResponse(BaseModel):
    """Aggregated statistics response."""

    total_views: int
    total_clicks: int
    avg_ctr: float
    total_marketplace_clicks: int


class DailyMetricsResponse(BaseModel):
    """Daily metrics for chart."""

    date: str
    total_views: int
    total_clicks: int


class RecommendationRequest(BaseModel):
    """Request for AI recommendations."""

    content_ids: list[UUID] = Field(default_factory=list)
    platform: str | None = None


class ContentRecommendationResponse(BaseModel):
    """AI recommendation for content optimization."""

    content_id: str
    recommendations: list[str]
    score: float = Field(ge=0.0, le=100.0)


class PublishTimeRecommendationResponse(BaseModel):
    """AI recommendation for publish time."""

    platform: str
    recommended_times: list[str]
    reasoning: str
