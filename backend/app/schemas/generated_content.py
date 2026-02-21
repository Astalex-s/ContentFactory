"""Generated content schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.generated_content import Platform, Tone


class GenerateContentRequest(BaseModel):
    """Request schema for content generation."""

    platform: Platform = Field(..., description="Target platform")
    tone: Tone = Field(..., description="Content tone")


class GeneratedVariantResponse(BaseModel):
    """Single generated variant in response."""

    id: UUID
    text: str
    variant: int


class GenerateContentResponse(BaseModel):
    """Response schema for content generation."""

    product_id: UUID
    generated_variants: list[GeneratedVariantResponse]


class GeneratedContentRead(BaseModel):
    """Read schema for generated content."""

    model_config = {"from_attributes": True}

    id: UUID
    product_id: UUID
    content_type: str
    content_text: Optional[str]
    file_path: Optional[str]
    status: str
    content_variant: int
    platform: str
    tone: str
    ai_model: Optional[str]
    created_at: datetime
