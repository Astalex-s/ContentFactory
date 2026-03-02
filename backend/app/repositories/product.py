"""Product repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.generated_content import ContentStatus, ContentType, GeneratedContent
from app.models.product import Product
from app.models.publication_queue import PublicationQueue, PublicationStatus


def _apply_filters(query, category: str | None, min_price: float | None, max_price: float | None):
    """Apply filter expressions to query."""
    if category:
        query = query.where(Product.category == category)
    if min_price is not None:
        query = query.where(Product.price >= min_price)
    if max_price is not None:
        query = query.where(Product.price <= max_price)
    return query


class ProductRepository:
    """Repository for Product CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, product: Product) -> Product:
        """Create single product."""
        self.session.add(product)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def bulk_create(self, products: list[Product]) -> list[Product]:
        """Create multiple products."""
        self.session.add_all(products)
        await self.session.flush()
        for p in products:
            await self.session.refresh(p)
        return products

    async def get_by_id(self, product_id: UUID) -> Product | None:
        """Get product by ID."""
        result = await self.session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

    async def get_unique_categories(self) -> list[str]:
        """Get all unique categories (non-null)."""
        result = await self.session.execute(
            select(Product.category)
            .distinct()
            .where(Product.category.isnot(None))
            .order_by(Product.category)
        )
        return [cat for cat in result.scalars().all() if cat]

    async def get_image_data(self, product_id: UUID) -> bytes | None:
        """Get product image_data by ID."""
        result = await self.session.execute(
            select(Product.image_data).where(Product.id == product_id)
        )
        data = result.scalar_one_or_none()
        return data if data else None

    async def update(self, product: Product, **kwargs) -> Product:
        """Update product fields."""
        for k, v in kwargs.items():
            if hasattr(product, k):
                setattr(product, k, v)
        await self.session.flush()
        await self.session.refresh(product)
        return product

    async def check_duplicate(self, marketplace_url: str) -> bool:
        """Check if product with URL already exists."""
        result = await self.session.execute(
            select(Product.id).where(Product.marketplace_url == marketplace_url).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def delete_by_id(self, product_id: UUID) -> bool:
        """Delete product by ID. Returns True if deleted, False if not found."""
        result = await self.session.execute(delete(Product).where(Product.id == product_id))
        return (result.rowcount or 0) > 0  # type: ignore[union-attr]

    async def delete_all(self) -> int:
        """Delete all products. Returns number of deleted rows."""
        result = await self.session.execute(delete(Product))
        return result.rowcount or 0  # type: ignore[union-attr]

    async def get_all(
        self,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        sort_by: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[list[Product], int]:
        """
        Get products with filtering, pagination and sorting.
        Returns (products, total_count).
        """
        from sqlalchemy import func

        base_query = select(Product)
        base_query = _apply_filters(base_query, category, min_price, max_price)

        # Count total
        count_query = select(func.count(Product.id)).select_from(Product)
        count_query = _apply_filters(count_query, category, min_price, max_price)
        total_result = await self.session.execute(count_query)
        total = total_result.scalar_one() or 0

        # Sort
        if sort_by == "price":
            base_query = base_query.order_by(Product.price.asc().nullslast())
        elif sort_by == "popularity":
            base_query = base_query.order_by(Product.popularity_score.desc().nullslast())
        else:
            base_query = base_query.order_by(Product.created_at.desc())

        # Pagination
        offset = (page - 1) * page_size
        base_query = base_query.offset(offset).limit(page_size)

        result = await self.session.execute(base_query)
        products = list(result.scalars().all())
        return products, total

    async def get_content_status_by_product_ids(self, product_ids: list[UUID]) -> dict[UUID, str]:
        """
        For each product, determine content status from generated_content.
        Returns: no_content | text_ready | image_ready | video_ready | complete
        """
        if not product_ids:
            return {}
        result = await self.session.execute(
            select(GeneratedContent.product_id, GeneratedContent.content_type)
            .where(GeneratedContent.product_id.in_(product_ids))
            .where(GeneratedContent.status == ContentStatus.READY)
        )
        rows = result.all()
        has_text = set()
        has_image = set()
        has_video = set()
        for pid, ctype in rows:
            if ctype == ContentType.TEXT:
                has_text.add(pid)
            elif ctype == ContentType.IMAGE:
                has_image.add(pid)
            elif ctype == ContentType.VIDEO:
                has_video.add(pid)
        out: dict[UUID, str] = {}
        for pid in product_ids:
            t = pid in has_text
            i = pid in has_image
            v = pid in has_video
            if t and i and v:
                out[pid] = "complete"
            elif v:
                out[pid] = "video_ready"
            elif i:
                out[pid] = "image_ready"
            elif t:
                out[pid] = "text_ready"
            else:
                out[pid] = "no_content"
        return out

    async def get_publication_status_by_product_ids(
        self, product_ids: list[UUID]
    ) -> dict[UUID, str]:
        """
        For each product, determine publication status from publication_queue
        (via generated_content). Returns: not_scheduled | scheduled | published | failed
        """
        if not product_ids:
            return {}
        # Join: product -> generated_content -> publication_queue
        stmt = (
            select(
                GeneratedContent.product_id,
                PublicationQueue.status,
            )
            .join(PublicationQueue, PublicationQueue.content_id == GeneratedContent.id)
            .where(GeneratedContent.product_id.in_(product_ids))
        )
        result = await self.session.execute(stmt)
        rows = result.all()
        # Priority: published > failed > scheduled > not_scheduled
        out: dict[UUID, str] = dict.fromkeys(product_ids, "not_scheduled")
        for pid, pstatus in rows:
            if pstatus == PublicationStatus.PUBLISHED:
                out[pid] = "published"
            elif pstatus == PublicationStatus.FAILED and out[pid] != "published":
                out[pid] = "failed"
            elif pstatus in (PublicationStatus.PENDING, PublicationStatus.PROCESSING):
                if out[pid] not in ("published", "failed"):
                    out[pid] = "scheduled"
        return out
