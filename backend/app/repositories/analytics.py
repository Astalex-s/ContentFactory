"""Analytics repository."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select, text
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
            existing.recorded_at = recorded_at or datetime.now(UTC)
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
            recorded_at=recorded_at or datetime.now(UTC),
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
        """Get aggregated statistics. Uses max(views) per (content_id, platform) to avoid double-counting."""
        subq = select(
            ContentMetrics.content_id,
            ContentMetrics.platform,
            func.max(ContentMetrics.views).label("views"),
            func.max(ContentMetrics.clicks).label("clicks"),
            func.max(ContentMetrics.ctr).label("ctr"),
            func.max(ContentMetrics.marketplace_clicks).label("marketplace_clicks"),
        ).group_by(ContentMetrics.content_id, ContentMetrics.platform)
        if platform:
            subq = subq.where(ContentMetrics.platform == platform.lower())
        subq = subq.subquery()
        result = await self.session.execute(
            select(
                func.sum(subq.c.views).label("total_views"),
                func.sum(subq.c.clicks).label("total_clicks"),
                func.avg(subq.c.ctr).label("avg_ctr"),
                func.sum(subq.c.marketplace_clicks).label("total_marketplace_clicks"),
            ).select_from(subq)
        )
        row = result.one()
        return {
            "total_views": row.total_views or 0,
            "total_clicks": row.total_clicks or 0,
            "avg_ctr": round(row.avg_ctr or 0.0, 2),
            "total_marketplace_clicks": row.total_marketplace_clicks or 0,
        }

    async def get_metrics_by_date(
        self, days: int = 30, platform: str | None = None
    ) -> list[dict]:
        """
        Get daily aggregated views and clicks.
        For each day, takes latest record per (content_id, platform), then sums.
        Returns list of {date, total_views, total_clicks} ordered by date.
        """
        since = (datetime.now(UTC) - timedelta(days=days)).date()
        platform_filter = "AND platform = :platform" if platform else ""
        stmt = text("""
            WITH ranked AS (
                SELECT content_id, platform,
                       (recorded_at AT TIME ZONE 'UTC')::date AS day,
                       views, clicks,
                       ROW_NUMBER() OVER (
                           PARTITION BY content_id, platform,
                                       (recorded_at AT TIME ZONE 'UTC')::date
                           ORDER BY recorded_at DESC
                       ) AS rn
                FROM content_metrics
                WHERE (recorded_at AT TIME ZONE 'UTC')::date >= :since
                """ + platform_filter + """
            )
            SELECT day, SUM(views)::int AS total_views, SUM(clicks)::int AS total_clicks
            FROM ranked
            WHERE rn = 1
            GROUP BY day
            ORDER BY day
        """)
        params: dict = {"since": since}
        if platform:
            params["platform"] = platform.lower()
        result = await self.session.execute(stmt, params)
        rows = result.fetchall()
        return [
            {
                "date": row.day.isoformat() if hasattr(row.day, "isoformat") else str(row.day),
                "total_views": row.total_views,
                "total_clicks": row.total_clicks,
            }
            for row in rows
        ]
