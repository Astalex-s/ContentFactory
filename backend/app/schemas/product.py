"""Product schemas."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field, HttpUrl


class ProductCreate(BaseModel):
    """Schema for product creation."""

    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=255)
    price: float = Field(..., gt=0)
    marketplace_url: HttpUrl | None = None


class ProductUpdate(BaseModel):
    """Schema for product update (partial)."""

    name: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    category: str | None = Field(None, max_length=255)
    price: float | None = Field(None, gt=0)


class ProductResponse(BaseModel):
    """Schema for product response."""

    model_config = {"from_attributes": True}

    id: UUID
    name: str
    description: str | None
    category: str | None
    price: float | None
    popularity_score: float | None
    marketplace_url: str | None
    image_filename: str | None


class ProductFilter(BaseModel):
    """Schema for product filtering."""

    category: str | None = None
    min_price: float | None = Field(None, gt=0)
    max_price: float | None = Field(None, gt=0)
    sort_by: str | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


class ProductListResponse(BaseModel):
    """Paginated list of products."""

    items: list[ProductResponse]
    total: int
    page: int
    page_size: int


class MarketplaceImportReport(BaseModel):
    """Report from marketplace import."""

    imported: int
    errors: list[str]
