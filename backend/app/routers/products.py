"""Products router."""

import io

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.dependencies import get_product_service
from app.schemas.product import ImportReport, ProductListResponse
from app.services.product import ProductService

router = APIRouter(prefix="/products", tags=["products"])


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


@router.post("/import", response_model=ImportReport)
async def import_products(
    file: UploadFile = File(..., description="CSV file with columns: name, description, category, price, marketplace_url"),
    service: ProductService = Depends(get_product_service),
) -> ImportReport:
    """Import products from CSV file."""
    content = await file.read()
    report = await service.import_from_csv(io.BytesIO(content))
    return ImportReport(**report)
