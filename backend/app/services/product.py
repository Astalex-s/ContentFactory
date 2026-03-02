"""Product service."""

from __future__ import annotations

import logging

from app.repositories.product import ProductRepository

logger = logging.getLogger(__name__)

# Приоритет по цене: popularity_score
# price < 500 → высокий (1.0)
# 500–800 → средний (0.5)
# >800 → низкий (0.2)
PRIORITY_HIGH = 1.0
PRIORITY_MEDIUM = 0.5
PRIORITY_LOW = 0.2


class ProductService:
    """Service for product business logic."""

    def __init__(self, repository: ProductRepository):
        self.repository = repository

    def calculate_popularity_score(self, price: float) -> float:
        """
        Calculate popularity score from price (priority-based).
        price < 500 → high (1.0), 500–800 → medium (0.5), >800 → low (0.2).
        """
        if price <= 0:
            return 0.0
        if price < 500:
            return PRIORITY_HIGH
        if price <= 800:
            return PRIORITY_MEDIUM
        return PRIORITY_LOW

    def get_priority(self, price: float) -> str:
        """Get priority label: высокий | средний | низкий."""
        if price <= 0:
            return "низкий"
        if price < 500:
            return "высокий"
        if price <= 800:
            return "средний"
        return "низкий"

    async def get_categories(self) -> list[str]:
        """Get all unique product categories."""
        return await self.repository.get_unique_categories()

    async def delete_product(self, product_id) -> bool:
        """Delete product by ID. Returns True if deleted, False if not found."""
        return await self.repository.delete_by_id(product_id)

    async def delete_all_products(self) -> int:
        """Delete all products. Returns number of deleted rows."""
        return await self.repository.delete_all()

    async def get_product(self, product_id) -> dict | None:
        """Get single product by ID."""
        from app.schemas.product import ProductResponse

        product = await self.repository.get_by_id(product_id)
        if product is None:
            return None
        return ProductResponse.model_validate(product).model_dump(mode="json")

    async def get_products(
        self,
        category: str | None = None,
        min_price: float | None = None,
        max_price: float | None = None,
        sort_by: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict:
        """
        Get products with filtering, pagination, sorting.
        Returns dict: items (list of ProductResponse), total, page, page_size.
        """
        from app.schemas.product import ProductResponse

        products, total = await self.repository.get_all(
            category=category,
            min_price=min_price,
            max_price=max_price,
            sort_by=sort_by,
            page=page,
            page_size=page_size,
        )
        product_ids = [p.id for p in products]
        content_map = await self.repository.get_content_status_by_product_ids(product_ids)
        pub_map = await self.repository.get_publication_status_by_product_ids(product_ids)
        items = []
        for p in products:
            d = ProductResponse.model_validate(p).model_dump(mode="json")
            d["content_status"] = content_map.get(p.id, "no_content")
            d["publication_status"] = pub_map.get(p.id, "not_scheduled")
            items.append(d)
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def get_product_image(self, product_id) -> bytes | None:
        """Get product image bytes from image_data."""
        return await self.repository.get_image_data(product_id)

    async def update_product(self, product_id, update_data) -> dict | None:
        """Update product by ID. Returns updated product dict or None if not found."""
        from app.schemas.product import ProductResponse, ProductUpdate

        product = await self.repository.get_by_id(product_id)
        if product is None:
            return None
        data = (
            update_data.model_dump(exclude_unset=True)
            if isinstance(update_data, ProductUpdate)
            else update_data
        )
        if not data:
            return ProductResponse.model_validate(product).model_dump(mode="json")
        if "price" in data and data["price"] is not None:
            data["popularity_score"] = self.calculate_popularity_score(data["price"])
        await self.repository.update(product, **data)
        return ProductResponse.model_validate(product).model_dump(mode="json")
