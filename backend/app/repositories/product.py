"""Product repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product import Product


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
        return result.rowcount > 0

    async def delete_all(self) -> int:
        """Delete all products. Returns number of deleted rows."""
        result = await self.session.execute(delete(Product))
        return result.rowcount or 0

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
