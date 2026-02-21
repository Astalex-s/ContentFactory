"""Products router."""

from __future__ import annotations

import io
from typing import Optional

from uuid import UUID

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile

from app.dependencies import get_product_service
from app.schemas.product import ImportReport, ProductListResponse, ProductResponse
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["products"])


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(
    product_id: UUID,
    service: ProductService = Depends(get_product_service),
) -> ProductResponse:
    """Get product by ID."""
    result = await service.get_product(product_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return ProductResponse(**result)


@router.get("", response_model=ProductListResponse)
async def get_products(
    category: Optional[str] = Query(None, description="Filter by category"),
    min_price: Optional[float] = Query(None, gt=0, description="Minimum price"),
    max_price: Optional[float] = Query(None, gt=0, description="Maximum price"),
    sort_by: Optional[str] = Query(None, description="Sort: price | popularity"),
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


@router.post("/import", response_model=ImportReport)
async def import_products(
    file: UploadFile = File(..., description="CSV file with columns: name, description, category, price, marketplace_url"),
    service: ProductService = Depends(get_product_service),
) -> ImportReport:
    """Import products from CSV file."""
    content = await file.read()
    report = await service.import_from_csv(io.BytesIO(content))
    return ImportReport(**report)
