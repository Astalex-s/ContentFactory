"""Analytics service."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.repositories.analytics import AnalyticsRepository


class AnalyticsService:
    """Service for analytics operations."""

    def __init__(self, analytics_repository: AnalyticsRepository):
        self.analytics_repo = analytics_repository

    async def record_metrics(
        self,
        content_id: UUID,
        platform: str,
        views: int,
        clicks: int,
        marketplace_clicks: int = 0,
        recorded_at: datetime | None = None,
    ) -> dict:
        """Record or update metrics for content."""
        metrics = await self.analytics_repo.create_or_update_metrics(
            content_id=content_id,
            platform=platform,
            views=views,
            clicks=clicks,
            marketplace_clicks=marketplace_clicks,
            recorded_at=recorded_at,
        )
        return {
            "id": str(metrics.id),
            "content_id": str(metrics.content_id),
            "platform": metrics.platform,
            "views": metrics.views,
            "clicks": metrics.clicks,
            "ctr": metrics.ctr,
            "marketplace_clicks": metrics.marketplace_clicks,
            "recorded_at": metrics.recorded_at.isoformat(),
        }

    async def get_content_metrics(self, content_id: UUID) -> list[dict]:
        """Get all metrics for a content."""
        metrics_list = await self.analytics_repo.get_metrics_by_content(content_id)
        return [
            {
                "id": str(m.id),
                "content_id": str(m.content_id),
                "platform": m.platform,
                "views": m.views,
                "clicks": m.clicks,
                "ctr": m.ctr,
                "marketplace_clicks": m.marketplace_clicks,
                "recorded_at": m.recorded_at.isoformat(),
            }
            for m in metrics_list
        ]

    async def get_latest_metrics(self, content_id: UUID) -> dict | None:
        """Get latest metrics for a content."""
        metrics = await self.analytics_repo.get_latest_metrics_by_content(content_id)
        if not metrics:
            return None
        return {
            "id": str(metrics.id),
            "content_id": str(metrics.content_id),
            "platform": metrics.platform,
            "views": metrics.views,
            "clicks": metrics.clicks,
            "ctr": metrics.ctr,
            "marketplace_clicks": metrics.marketplace_clicks,
            "recorded_at": metrics.recorded_at.isoformat(),
        }

    async def get_top_content(self, limit: int = 10, platform: str | None = None) -> list[dict]:
        """Get top performing content."""
        return await self.analytics_repo.get_top_content_by_views(limit=limit, platform=platform)

    async def get_aggregated_stats(self, platform: str | None = None) -> dict:
        """Get aggregated statistics."""
        return await self.analytics_repo.get_aggregated_stats(platform=platform)

    async def get_metrics_by_date(self, days: int = 30, platform: str | None = None) -> list[dict]:
        """Get daily aggregated views and clicks for charts."""
        return await self.analytics_repo.get_metrics_by_date(days=days, platform=platform)

    async def get_latest_metrics_map(
        self, content_platform_pairs: list[tuple[UUID, str]]
    ) -> dict[tuple[UUID, str], dict]:
        """Get latest metrics for (content_id, platform) pairs. Returns map of key -> metrics dict."""
        raw = await self.analytics_repo.get_latest_metrics_map(content_platform_pairs)
        return {
            k: {
                "id": str(v.id),
                "content_id": str(v.content_id),
                "platform": v.platform,
                "views": v.views,
                "clicks": v.clicks,
                "ctr": v.ctr,
                "marketplace_clicks": v.marketplace_clicks,
                "recorded_at": v.recorded_at.isoformat(),
            }
            for k, v in raw.items()
        }
