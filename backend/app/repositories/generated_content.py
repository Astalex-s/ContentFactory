"""Generated content repository."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_content import (
    ContentStatus,
    ContentTextType,
    ContentType,
    GeneratedContent,
    Platform,
    Tone,
)


class GeneratedContentRepository:
    """Repository for GeneratedContent CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        product_id: UUID,
        content_text: str,
        content_variant: int,
        platform: Platform,
        tone: Tone,
        content_text_type: ContentTextType = ContentTextType.SHORT_POST,
        ai_model: str | None = None,
        status: ContentStatus = ContentStatus.DRAFT,
    ) -> GeneratedContent:
        """Create single generated content record."""
        content = GeneratedContent(
            product_id=product_id,
            content_type=ContentType.TEXT,
            content_text=content_text[:2000] if content_text else None,
            content_variant=content_variant,
            platform=platform,
            tone=tone,
            content_text_type=content_text_type,
            ai_model=ai_model,
            status=status,
        )
        self.session.add(content)
        await self.session.flush()
        await self.session.refresh(content)
        return content

    async def create_media(
        self,
        product_id: UUID,
        content_type: ContentType,
        file_path: str,
        content_variant: int = 1,
        content_text: str | None = None,
        ai_model: str | None = None,
        status: ContentStatus = ContentStatus.READY,
    ) -> GeneratedContent:
        """Create IMAGE or VIDEO content record."""
        content = GeneratedContent(
            product_id=product_id,
            content_type=content_type,
            content_text=content_text[:2000] if content_text else None,
            file_path=file_path,
            content_variant=content_variant,
            platform=Platform.YOUTUBE,
            tone=Tone.NEUTRAL,
            content_text_type=ContentTextType.SHORT_POST,
            ai_model=ai_model,
            status=status,
        )
        self.session.add(content)
        await self.session.flush()
        await self.session.refresh(content)
        return content

    async def get_by_id(self, content_id: UUID) -> GeneratedContent | None:
        """Get content by ID."""
        result = await self.session.execute(
            select(GeneratedContent).where(GeneratedContent.id == content_id)
        )
        return result.scalar_one_or_none()

    async def get_by_ids(self, content_ids: list[UUID]) -> dict[UUID, GeneratedContent]:
        """Get content by IDs. Returns dict content_id -> content."""
        if not content_ids:
            return {}
        result = await self.session.execute(
            select(GeneratedContent).where(GeneratedContent.id.in_(content_ids))
        )
        items = list(result.scalars().all())
        return {c.id: c for c in items}

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[GeneratedContent], int]:
        """Get all content with pagination. Returns (items, total)."""
        from sqlalchemy import func

        count_result = await self.session.execute(select(func.count(GeneratedContent.id)))
        total = count_result.scalar_one() or 0

        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(GeneratedContent)
            .order_by(GeneratedContent.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        return items, total

    async def get_by_product(
        self,
        product_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[GeneratedContent], int]:
        """Get content list by product with pagination. Returns (items, total)."""
        from sqlalchemy import func

        count_result = await self.session.execute(
            select(func.count(GeneratedContent.id)).where(GeneratedContent.product_id == product_id)
        )
        total = count_result.scalar_one() or 0

        offset = (page - 1) * page_size
        result = await self.session.execute(
            select(GeneratedContent)
            .where(GeneratedContent.product_id == product_id)
            .order_by(GeneratedContent.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        items = list(result.scalars().all())
        return items, total

    async def update_text(self, content_id: UUID, content_text: str) -> GeneratedContent | None:
        """Update content_text. Returns updated content or None."""
        content = await self.get_by_id(content_id)
        if content is None or content.status != ContentStatus.DRAFT:
            return None
        content.content_text = content_text[:2000] if content_text else None
        await self.session.flush()
        await self.session.refresh(content)
        return content

    async def set_approved_for_publication(
        self, content_id: UUID, approved: bool
    ) -> GeneratedContent | None:
        """Set approved_for_publication flag. Returns updated content or None."""
        content = await self.get_by_id(content_id)
        if content is None:
            return None
        content.approved_for_publication = approved
        await self.session.flush()
        await self.session.refresh(content)
        return content

    async def get_ready_for_auto_publish(
        self, min_age_minutes: int = 5, limit: int = 20
    ) -> list[GeneratedContent]:
        """Get video content ready for auto-publish: ready, approved, created_at + min_age <= now."""
        cutoff = datetime.now(UTC) - timedelta(minutes=min_age_minutes)
        result = await self.session.execute(
            select(GeneratedContent)
            .where(GeneratedContent.content_type == ContentType.VIDEO)
            .where(GeneratedContent.status == ContentStatus.READY)
            .where(GeneratedContent.approved_for_publication.is_(True))
            .where(GeneratedContent.created_at <= cutoff)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def delete(self, content_id: UUID) -> bool:
        """Delete content by ID. Returns True if deleted."""
        content = await self.get_by_id(content_id)
        if content is None:
            return False
        await self.session.delete(content)
        await self.session.flush()
        return True
