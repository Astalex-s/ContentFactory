"""Product service."""

from __future__ import annotations

import csv
import io
import logging
from typing import BinaryIO

from app.models.product import Product
from app.repositories.product import ProductRepository

logger = logging.getLogger(__name__)


REQUIRED_COLUMNS = {"name", "description", "category", "price", "marketplace_url"}

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
        items = [ProductResponse.model_validate(p) for p in products]
        return {"items": items, "total": total, "page": page, "page_size": page_size}

    async def import_from_csv(self, file: BinaryIO) -> dict:
        """
        Import products from CSV file.
        Returns report: total_rows, imported, skipped, errors.
        """
        content = file.read().decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(content))
        if not reader.fieldnames:
            return {"total_rows": 0, "imported": 0, "skipped": 0, "errors": ["Empty file"]}

        cols = set(c.strip() for c in reader.fieldnames if c)
        missing = REQUIRED_COLUMNS - cols
        if missing:
            return {
                "total_rows": 0,
                "imported": 0,
                "skipped": 0,
                "errors": [f"Missing columns: {missing}"],
            }

        imported = 0
        skipped = 0
        errors: list[str] = []
        to_create: list[Product] = []
        seen_urls: set[str] = set()

        for row_num, row in enumerate(reader, start=2):
            try:
                name = (row.get("name") or "").strip()
                if not name:
                    errors.append(f"Row {row_num}: empty name")
                    skipped += 1
                    continue

                price_str = (row.get("price") or "").strip().replace(",", ".")
                try:
                    price = float(price_str)
                except ValueError:
                    errors.append(f"Row {row_num}: invalid price '{price_str}'")
                    skipped += 1
                    continue
                if price <= 0:
                    errors.append(f"Row {row_num}: price must be > 0")
                    skipped += 1
                    continue

                marketplace_url = (row.get("marketplace_url") or "").strip()
                if marketplace_url:
                    if await self.repository.check_duplicate(marketplace_url):
                        skipped += 1
                        continue
                    if marketplace_url in seen_urls:
                        skipped += 1
                        continue
                    seen_urls.add(marketplace_url)

                description = (row.get("description") or "").strip() or None
                category = (row.get("category") or "").strip() or None
                popularity_score = self.calculate_popularity_score(price)

                image_index = len(to_create) % 19
                image_filename = f"product_{image_index:02d}.png"
                product = Product(
                    name=name,
                    description=description,
                    category=category,
                    price=price,
                    popularity_score=popularity_score,
                    marketplace_url=marketplace_url or None,
                    image_filename=image_filename,
                )
                to_create.append(product)
                imported += 1

            except Exception as e:
                errors.append(f"Row {row_num}: {str(e)}")
                skipped += 1

        if to_create:
            await self.repository.bulk_create(to_create)

        total_rows = imported + skipped
        logger.info(
            "CSV import completed: imported=%d, skipped=%d, total_rows=%d",
            imported,
            skipped,
            total_rows,
        )
        return {
            "total_rows": total_rows,
            "imported": imported,
            "skipped": skipped,
            "errors": errors,
        }
