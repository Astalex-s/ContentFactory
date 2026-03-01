"""Content management service."""

from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from app.repositories.generated_content import GeneratedContentRepository
from app.schemas.generated_content import ContentListResponse, GeneratedContentRead

if TYPE_CHECKING:
    from app.interfaces.storage import StorageInterface


class ContentService:
    """Service for content list, update, delete."""

    def __init__(self, content_repository: GeneratedContentRepository):
        self.content_repo = content_repository

    async def get_all(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> ContentListResponse:
        """Get paginated content list for all products."""
        items, total = await self.content_repo.get_all(
            page=page,
            page_size=page_size,
        )
        return ContentListResponse(
            items=[GeneratedContentRead.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_by_product(
        self,
        product_id: UUID,
        page: int = 1,
        page_size: int = 20,
    ) -> ContentListResponse:
        """Get paginated content list for product."""
        items, total = await self.content_repo.get_by_product(
            product_id=product_id,
            page=page,
            page_size=page_size,
        )
        return ContentListResponse(
            items=[GeneratedContentRead.model_validate(c) for c in items],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get_by_ids(self, content_ids: list[UUID]):
        """Get content by IDs. Returns dict content_id -> GeneratedContent."""
        return await self.content_repo.get_by_ids(content_ids)

    async def has_content(self, product_id: UUID) -> bool:
        """Check if product has any generated content."""
        _, total = await self.content_repo.get_by_product(
            product_id=product_id,
            page=1,
            page_size=1,
        )
        return total > 0

    async def update_text(self, content_id: UUID, content_text: str) -> GeneratedContentRead | None:
        """Update content text (draft only). Returns None if not found or not draft."""
        content = await self.content_repo.update_text(content_id, content_text)
        if content is None:
            return None
        return GeneratedContentRead.model_validate(content)

    async def delete(self, content_id: UUID, media: StorageInterface | None = None) -> bool:
        """Delete content. Returns True if deleted. If media provided, also deletes file."""
        content = await self.content_repo.get_by_id(content_id)
        if content is None:
            return False
        if media and content.file_path:
            await media.delete(content.file_path)
        return await self.content_repo.delete(content_id)
