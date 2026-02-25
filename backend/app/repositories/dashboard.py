"""Dashboard repository."""

from __future__ import annotations

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.content_metrics import ContentMetrics
from app.models.generated_content import ContentType, GeneratedContent
from app.models.product import Product
from app.models.publication_queue import PublicationQueue, PublicationStatus


class DashboardRepository:
    """Repository for Dashboard aggregation queries."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_total_products(self) -> int:
        """Get total number of products."""
        result = await self.session.execute(select(func.count(Product.id)))
        return result.scalar_one() or 0

    async def get_products_with_content_count(self) -> int:
        """Get count of products that have at least one generated content."""
        result = await self.session.execute(
            select(func.count(func.distinct(GeneratedContent.product_id)))
        )
        return result.scalar_one() or 0

    async def get_text_generated_count(self) -> int:
        """Get count of products with text content."""
        result = await self.session.execute(
            select(func.count(func.distinct(GeneratedContent.product_id))).where(
                GeneratedContent.content_type == ContentType.TEXT
            )
        )
        return result.scalar_one() or 0

    async def get_media_generated_count(self) -> int:
        """Get count of products with image or video content."""
        result = await self.session.execute(
            select(func.count(func.distinct(GeneratedContent.product_id))).where(
                GeneratedContent.content_type.in_([ContentType.IMAGE, ContentType.VIDEO])
            )
        )
        return result.scalar_one() or 0

    async def get_scheduled_count(self) -> int:
        """Get count of scheduled publications."""
        result = await self.session.execute(
            select(func.count(PublicationQueue.id)).where(
                PublicationQueue.status.in_(
                    [PublicationStatus.PENDING, PublicationStatus.PROCESSING]
                )
            )
        )
        return result.scalar_one() or 0

    async def get_published_count(self) -> int:
        """Get count of published items."""
        result = await self.session.execute(
            select(func.count(PublicationQueue.id)).where(
                PublicationQueue.status == PublicationStatus.PUBLISHED
            )
        )
        return result.scalar_one() or 0

    async def get_failed_publication_count(self) -> int:
        """Get count of failed publications."""
        result = await self.session.execute(
            select(func.count(PublicationQueue.id)).where(
                PublicationQueue.status == PublicationStatus.FAILED
            )
        )
        return result.scalar_one() or 0

    async def get_analytics_count(self) -> int:
        """Get count of content items with recorded metrics."""
        result = await self.session.execute(
            select(func.count(func.distinct(ContentMetrics.content_id)))
        )
        return result.scalar_one() or 0

    async def get_low_ctr_count(self, threshold: float = 2.0) -> int:
        """Get count of content items with CTR below threshold."""
        result = await self.session.execute(
            select(func.count(ContentMetrics.id)).where(ContentMetrics.ctr < threshold)
        )
        return result.scalar_one() or 0
