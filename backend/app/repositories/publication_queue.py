"""Publication queue repository."""

from __future__ import annotations

from datetime import UTC, datetime
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
        privacy_status: str = "private",
        vk_group_id: str | None = None,
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
            privacy_status=privacy_status,
            vk_group_id=vk_group_id,
        )
        self.session.add(entry)
        await self.session.flush()
        await self.session.refresh(entry)
        return entry

    async def has_content_scheduled(self, content_id: UUID) -> bool:
        """Check if content is already in queue (any status)."""
        result = await self.session.execute(
            select(PublicationQueue.id).where(PublicationQueue.content_id == content_id).limit(1)
        )
        return result.scalar_one_or_none() is not None

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

    async def get_published_with_video_id(
        self, platform: str | None = None, limit: int = 500
    ) -> list[PublicationQueue]:
        """Get entries with PUBLISHED or PROCESSING status and platform_video_id set."""
        from sqlalchemy import or_

        query = (
            select(PublicationQueue)
            .where(
                or_(
                    PublicationQueue.status == PublicationStatus.PUBLISHED,
                    PublicationQueue.status == PublicationStatus.PROCESSING,
                )
            )
            .where(PublicationQueue.platform_video_id.isnot(None))
            .where(PublicationQueue.platform_video_id != "")
        )
        if platform:
            query = query.where(PublicationQueue.platform == platform.lower())
        query = query.order_by(PublicationQueue.scheduled_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_platform_video_ids(
        self, content_platform_pairs: list[tuple[UUID, str]]
    ) -> dict[tuple[UUID, str], str]:
        """Get platform_video_id for (content_id, platform) pairs.
        Returns only PUBLISHED/PROCESSING entries with non-empty platform_video_id.
        """
        if not content_platform_pairs:
            return {}
        content_ids = list({cp[0] for cp in content_platform_pairs})
        platforms = list({cp[1].lower() for cp in content_platform_pairs})
        from sqlalchemy import or_

        result = await self.session.execute(
            select(
                PublicationQueue.content_id,
                PublicationQueue.platform,
                PublicationQueue.platform_video_id,
            )
            .where(
                or_(
                    PublicationQueue.status == PublicationStatus.PUBLISHED,
                    PublicationQueue.status == PublicationStatus.PROCESSING,
                )
            )
            .where(PublicationQueue.content_id.in_(content_ids))
            .where(PublicationQueue.platform.in_(platforms))
            .where(PublicationQueue.platform_video_id.isnot(None))
            .where(PublicationQueue.platform_video_id != "")
        )
        rows = result.all()
        return {
            (r.content_id, r.platform): r.platform_video_id for r in rows if r.platform_video_id
        }

    async def get_pending(self, limit: int = 10) -> list[PublicationQueue]:
        """Get pending entries ready to process (scheduled_at <= now)."""
        result = await self.session.execute(
            select(PublicationQueue)
            .where(PublicationQueue.status == PublicationStatus.PENDING)
            .where(PublicationQueue.scheduled_at <= datetime.now(UTC))
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

    async def get_all(
        self,
        status: PublicationStatus | None = None,
        platform: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[PublicationQueue]:
        """Get all publications with optional filters."""
        query = select(PublicationQueue)

        if status:
            query = query.where(PublicationQueue.status == status)
        if platform:
            query = query.where(PublicationQueue.platform == platform.lower())

        query = query.order_by(PublicationQueue.scheduled_at.desc())
        query = query.limit(limit).offset(offset)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_all(
        self,
        status: PublicationStatus | None = None,
        platform: str | None = None,
    ) -> int:
        """Count publications with optional filters."""
        from sqlalchemy import func

        query = select(func.count(PublicationQueue.id))

        if status:
            query = query.where(PublicationQueue.status == status)
        if platform:
            query = query.where(PublicationQueue.platform == platform.lower())

        result = await self.session.execute(query)
        return result.scalar_one()

    async def delete(self, queue_id: UUID) -> bool:
        """Delete publication queue entry. Returns True if deleted."""
        entry = await self.get_by_id(queue_id)
        if entry is None:
            return False
        await self.session.delete(entry)
        await self.session.flush()
        return True

    async def bulk_create(
        self,
        publications: list[dict],
    ) -> list[PublicationQueue]:
        """Create multiple publication queue entries."""
        entries = []
        for pub in publications:
            entry = PublicationQueue(
                content_id=pub["content_id"],
                platform=pub["platform"],
                account_id=pub["account_id"],
                scheduled_at=pub["scheduled_at"],
                status=PublicationStatus.PENDING,
                title=pub.get("title"),
                description=pub.get("description"),
                privacy_status=pub.get("privacy_status", "private"),
                vk_group_id=pub.get("vk_group_id"),
            )
            self.session.add(entry)
            entries.append(entry)

        await self.session.flush()
        for entry in entries:
            await self.session.refresh(entry)
        return entries
