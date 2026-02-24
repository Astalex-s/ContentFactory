"""Publication queue repository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.publication_queue import PublicationQueue, PublicationStatus


class PublicationQueueRepository:
    """Repository for PublicationQueue CRUD."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        content_id: UUID,
        platform: str,
        account_id: UUID,
        scheduled_at: datetime,
        title: str | None = None,
        description: str | None = None,
    ) -> PublicationQueue:
        """Create publication queue entry."""
        entry = PublicationQueue(
            content_id=content_id,
            platform=platform,
            account_id=account_id,
            scheduled_at=scheduled_at,
            status=PublicationStatus.PENDING,
            title=title,
            description=description,
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def get_by_id(self, queue_id: UUID) -> PublicationQueue | None:
        """Get queue entry by ID."""
        result = await self.session.execute(
            select(PublicationQueue).where(PublicationQueue.id == queue_id)
        )
        return result.scalar_one_or_none()

    async def get_processing(self, limit: int = 20) -> list[PublicationQueue]:
        """Get entries in PROCESSING status (for status sync)."""
        result = await self.session.execute(
            select(PublicationQueue)
            .where(PublicationQueue.status == PublicationStatus.PROCESSING)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_pending(self, limit: int = 10) -> list[PublicationQueue]:
        """Get pending entries ready to process (scheduled_at <= now)."""
        result = await self.session.execute(
            select(PublicationQueue)
            .where(PublicationQueue.status == PublicationStatus.PENDING)
            .where(PublicationQueue.scheduled_at <= datetime.now(timezone.utc))
            .order_by(PublicationQueue.scheduled_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        queue_id: UUID,
        status: PublicationStatus,
        error_message: str | None = None,
        platform_video_id: str | None = None,
    ) -> PublicationQueue | None:
        """Update queue entry status."""
        entry = await self.get_by_id(queue_id)
        if entry is None:
            return None
        entry.status = status
        if error_message is not None:
            entry.error_message = error_message
        if platform_video_id is not None:
            entry.platform_video_id = platform_video_id
        await self.session.flush()
        await self.session.refresh(entry)
        return entry
