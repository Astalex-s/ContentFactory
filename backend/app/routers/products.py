"""Products router."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response

from app.dependencies import get_marketplace_import_service, get_product_service
from app.schemas.product import (
    MarketplaceImportReport,
    ProductListResponse,
    ProductResponse,
    ProductUpdate,
)
from app.services.marketplace_import import MarketplaceImportService
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/categories", response_model=list[str])
async def get_categories(
    service: ProductService = Depends(get_product_service),
) -> list[str]:
    """Get all unique product categories."""
    return await service.get_categories()


@router.get("", response_model=ProductListResponse)
async def get_products(
    category: str | None = Query(None, description="Filter by category"),
    min_price: float | None = Query(None, gt=0, description="Minimum price"),
    max_price: float | None = Query(None, gt=0, description="Maximum price"),
    sort_by: str | None = Query(None, description="Sort: price | popularity"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ProductService = Depends(get_product_service),
) -> ProductListResponse:
    """Get products with filters and pagination."""
    result = await service.get_products(
        category=category,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return ProductListResponse(**result)


@router.delete("/all", status_code=200)
async def delete_all_products(
    service: ProductService = Depends(get_product_service),
) -> dict:
    """Delete all products. Returns count of deleted items."""
    count = await service.delete_all_products()
    return {"deleted": count}


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Get product by ID."""
    result = await service.get_product(product_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return ProductResponse(**result)


@router.get("/{product_id}/image")
async def get_product_image(
    product_id: UUID,
    service: ProductService = Depends(get_product_service),
) -> Response:
    """Get product image (PNG) from image_data."""
    data = await service.get_product_image(product_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Изображение не найдено")
    return Response(content=data, media_type="image/png")


@router.delete("/{product_id}", status_code=204)
async def delete_product(
    product_id: UUID,
    service: ProductService = Depends(get_product_service),
) -> None:
    """Delete product by ID."""
    deleted = await service.delete_product(product_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Товар не найден")


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: UUID,
    body: ProductUpdate,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Update product by ID."""
    result = await service.update_product(product_id, body)
    if result is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return ProductResponse(**result)


@router.post("/import-from-marketplace", response_model=MarketplaceImportReport)
async def import_from_marketplace(
    service: MarketplaceImportService = Depends(get_marketplace_import_service),
) -> MarketplaceImportReport:
    """Import 5 products from marketplace (GPT + Replicate)."""
    report = await service.import_from_marketplace()
    return MarketplaceImportReport(**report)
