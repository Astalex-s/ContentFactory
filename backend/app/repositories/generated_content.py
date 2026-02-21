"""Generated content repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_content import (
    ContentStatus,
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
        ai_model: str | None = None,
        status: ContentStatus = ContentStatus.DRAFT,
    ) -> GeneratedContent:
        """Create single generated content record."""
        content = GeneratedContent(
            product_id=product_id,
            content_type=ContentType.TEXT,
            content_text=content_text[:800] if content_text else None,
            content_variant=content_variant,
            platform=platform,
            tone=tone,
            ai_model=ai_model,
            status=status,
        )
        self.session.add(content)
        await self.session.flush()
        await self.session.refresh(content)
        return content
