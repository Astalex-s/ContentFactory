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

    async def get_latest_metrics_by_content_platform(
        self, content_id: UUID, platform: str
    ) -> ContentMetrics | None:
        """Get latest metrics for a (content_id, platform) pair."""
        result = await self.session.execute(
            select(ContentMetrics)
            .where(ContentMetrics.content_id == content_id)
            .where(ContentMetrics.platform == platform.lower())
            .order_by(ContentMetrics.recorded_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_latest_metrics_map(
        self, content_platform_pairs: list[tuple[UUID, str]]
    ) -> dict[tuple[UUID, str], ContentMetrics]:
        """Get latest metrics for multiple (content_id, platform) pairs. Returns map."""
        if not content_platform_pairs:
            return {}
        content_ids = list({cp[0] for cp in content_platform_pairs})
        platforms = list({cp[1].lower() for cp in content_platform_pairs})
        result = await self.session.execute(
            select(ContentMetrics)
            .where(ContentMetrics.content_id.in_(content_ids))
            .where(ContentMetrics.platform.in_(platforms))
            .order_by(ContentMetrics.recorded_at.desc())
        )
        rows = result.scalars().all()
        seen: set[tuple[UUID, str]] = set()
        out: dict[tuple[UUID, str], ContentMetrics] = {}
        for r in rows:
            key = (r.content_id, r.platform)
            if key not in seen:
                seen.add(key)
                out[key] = r
        return out

    async def get_top_content_by_views(
        self, limit: int = 10, platform: str | None = None
    ) -> list[dict]:
        """Get top content by views. Uses only latest metrics per (content_id, platform)."""
        query = select(ContentMetrics).order_by(
            ContentMetrics.content_id,
            ContentMetrics.platform,
            ContentMetrics.recorded_at.desc(),
        )
        if platform:
            query = query.where(ContentMetrics.platform == platform.lower())
        result = await self.session.execute(query)
        rows = result.scalars().all()
        seen: set[tuple[UUID, str]] = set()
        latest: list[ContentMetrics] = []
        for r in rows:
            key = (r.content_id, r.platform)
            if key not in seen:
                seen.add(key)
                latest.append(r)
        sorted_by_views = sorted(latest, key=lambda m: m.views, reverse=True)[:limit]
        return [
            {
                "content_id": str(m.content_id),
                "platform": m.platform,
                "views": m.views,
                "clicks": m.clicks,
                "ctr": m.ctr,
            }
            for m in sorted_by_views
        ]

    async def get_aggregated_stats(self, platform: str | None = None) -> dict:
        """Get aggregated statistics. Uses only latest metrics per (content_id, platform)."""
        query = select(ContentMetrics).order_by(
            ContentMetrics.content_id,
            ContentMetrics.platform,
            ContentMetrics.recorded_at.desc(),
        )
        if platform:
            query = query.where(ContentMetrics.platform == platform.lower())
        result = await self.session.execute(query)
        rows = result.scalars().all()
        # Keep only latest per (content_id, platform)
        seen: set[tuple[UUID, str]] = set()
        latest: list[ContentMetrics] = []
        for r in sorted(rows, key=lambda x: (x.content_id, x.platform, x.recorded_at), reverse=True):
            key = (r.content_id, r.platform)
            if key not in seen:
                seen.add(key)
                latest.append(r)
        total_views = sum(m.views for m in latest)
        total_clicks = sum(m.clicks for m in latest)
        avg_ctr = (sum(m.ctr for m in latest) / len(latest)) if latest else 0.0
        total_marketplace = sum(m.marketplace_clicks for m in latest)
        return {
            "total_views": total_views,
            "total_clicks": total_clicks,
            "avg_ctr": round(avg_ctr, 2),
            "total_marketplace_clicks": total_marketplace,
        }
