"""Product schemas."""

from __future__ import annotations

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field


class ProductCreate(BaseModel):
    """Schema for product creation."""

    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=255)
    price: float = Field(..., gt=0)
    marketplace_url: Optional[str] = Field(None, max_length=512)


class ProductUpdate(BaseModel):
    """Schema for product update (partial)."""

    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=255)
    price: Optional[float] = Field(None, gt=0)


class ProductResponse(BaseModel):
    """Schema for product response."""

    model_config = {"from_attributes": True}

    id: UUID
    name: str
    description: Optional[str]
    category: Optional[str]
    price: Optional[float]
    popularity_score: Optional[float]
    marketplace_url: Optional[str]
    image_filename: Optional[str]


class ProductFilter(BaseModel):
    """Schema for product filtering."""

    category: Optional[str] = None
    min_price: Optional[float] = Field(None, gt=0)
    max_price: Optional[float] = Field(None, gt=0)
    sort_by: Optional[str] = None
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
