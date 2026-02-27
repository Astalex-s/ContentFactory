"""Analytics repository."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_metrics import ContentMetrics


class AnalyticsRepository:
    """Repository for ContentMetrics CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_or_update_metrics(
        self,
        content_id: UUID,
        platform: str,
        views: int,
        clicks: int,
        marketplace_clicks: int,
        recorded_at: datetime | None = None,
    ) -> ContentMetrics:
        """Create or update metrics for content."""
        ctr = (clicks / views * 100) if views > 0 else 0.0

        result = await self.session.execute(
            select(ContentMetrics)
            .where(ContentMetrics.content_id == content_id)
            .where(ContentMetrics.platform == platform)
            .order_by(ContentMetrics.recorded_at.desc())
            .limit(1)
        )
        existing = result.scalar_one_or_none()

        if existing and recorded_at and (recorded_at - existing.recorded_at).total_seconds() < 3600:
            existing.views = views
            existing.clicks = clicks
            existing.ctr = ctr
            existing.marketplace_clicks = marketplace_clicks
            existing.recorded_at = recorded_at or datetime.utcnow()
            await self.session.flush()
            await self.session.refresh(existing)
            return existing

        metrics = ContentMetrics(
            content_id=content_id,
            platform=platform,
            views=views,
            clicks=clicks,
            ctr=ctr,
            marketplace_clicks=marketplace_clicks,
            recorded_at=recorded_at or datetime.utcnow(),
        )
        self.session.add(metrics)
        await self.session.flush()
        await self.session.refresh(metrics)
        return metrics

    async def get_metrics_by_content(self, content_id: UUID) -> list[ContentMetrics]:
        """Get all metrics for a content."""
        result = await self.session.execute(
            select(ContentMetrics)
            .where(ContentMetrics.content_id == content_id)
            .order_by(ContentMetrics.recorded_at.desc())
        )
        return list(result.scalars().all())

    async def get_latest_metrics_by_content(self, content_id: UUID) -> ContentMetrics | None:
        """Get latest metrics for a content."""
        result = await self.session.execute(
            select(ContentMetrics)
            .where(ContentMetrics.content_id == content_id)
            .order_by(ContentMetrics.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_top_content_by_views(
        self, limit: int = 10, platform: str | None = None
    ) -> list[dict]:
        """Get top content by views."""
        query = (
            select(
                ContentMetrics.content_id,
                ContentMetrics.platform,
                func.max(ContentMetrics.views).label("max_views"),
                func.max(ContentMetrics.clicks).label("max_clicks"),
                func.max(ContentMetrics.ctr).label("max_ctr"),
            )
            .group_by(ContentMetrics.content_id, ContentMetrics.platform)
            .order_by(func.max(ContentMetrics.views).desc())
            .limit(limit)
        )

        if platform:
            query = query.where(ContentMetrics.platform == platform)

        result = await self.session.execute(query)
        rows = result.all()

        return [
            {
                "content_id": str(row.content_id),
                "platform": row.platform,
                "views": row.max_views,
                "clicks": row.max_clicks,
                "ctr": row.max_ctr,
            }
            for row in rows
        ]

    async def get_aggregated_stats(self, platform: str | None = None) -> dict:
        """Get aggregated statistics."""
        query = select(
            func.sum(ContentMetrics.views).label("total_views"),
            func.sum(ContentMetrics.clicks).label("total_clicks"),
            func.avg(ContentMetrics.ctr).label("avg_ctr"),
            func.sum(ContentMetrics.marketplace_clicks).label("total_marketplace_clicks"),
        )

        if platform:
            query = query.where(ContentMetrics.platform == platform)

        result = await self.session.execute(query)
        row = result.one()

        return {
            "total_views": row.total_views or 0,
            "total_clicks": row.total_clicks or 0,
            "avg_ctr": round(row.avg_ctr or 0.0, 2),
            "total_marketplace_clicks": row.total_marketplace_clicks or 0,
        }
