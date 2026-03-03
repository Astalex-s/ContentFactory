"""Generated content schemas."""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.models.generated_content import ContentTextType, Platform, Tone


class GenerateContentRequest(BaseModel):
    """Request schema for content generation."""

    platform: Platform = Field(..., description="Target platform")
    tone: Tone = Field(..., description="Content tone")
    content_text_type: ContentTextType = Field(
        default=ContentTextType.SHORT_POST,
        description="Type of text to generate",
    )


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
    content_text_type: str
    content_text: str | None
    file_path: str | None
    status: str
    content_variant: int
    platform: str
    tone: str
    ai_model: str | None
    created_at: datetime
    approved_for_publication: bool = False


class ContentListResponse(BaseModel):
    """Paginated list of generated content."""

    items: list[GeneratedContentRead]
    total: int
    page: int
    page_size: int


class UpdateContentRequest(BaseModel):
    """Request schema for content update."""

    content_text: str = Field(..., min_length=1, max_length=2000)


class TaskResponse(BaseModel):
    """Task status response."""

    task_id: str
    status: str  # pending | running | completed | failed


class GeneratePostTextRequest(BaseModel):
    """Request for generating VK post text (title + body)."""

    video_url: str | None = Field(
        None, max_length=500, description="Optional video URL to include in post"
    )


class GeneratePostTextResponse(BaseModel):
    """Response with generated title and text for VK post."""

    title: str
    text: str


class CreatePostTextRequest(BaseModel):
    """Request to create text content for VK post."""

    title: str = Field(..., min_length=1, max_length=200)
    text: str = Field(..., min_length=1, max_length=2000)
    video_url: str | None = Field(None, max_length=500)
