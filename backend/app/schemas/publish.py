"""Pydantic schemas for publication."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class PublishRequest(BaseModel):
    """Request to schedule publication. content_id from path."""

    platform: str = Field(..., pattern="^(youtube|vk|tiktok)$")
    account_id: UUID
    scheduled_at: datetime | None = None
    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=5000)

    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_time(cls, v: datetime | None) -> datetime | None:
        """Allow now or past for immediate publish; future for scheduled."""
        if v is not None:
            if v.tzinfo is None:
                v = v.replace(tzinfo=UTC)
        return v


class PublishResponse(BaseModel):
    """Publication queue entry response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    content_id: UUID
    platform: str
    account_id: UUID
    scheduled_at: datetime
    status: str
    error_message: str | None
    platform_video_id: str | None
    created_at: datetime
    content_file_path: str | None = None
    content_type: str | None = None


class PublishStatusResponse(BaseModel):
    """Publication status response."""

    id: UUID
    status: str
    error_message: str | None
    platform_video_id: str | None


class BulkPublishRequest(BaseModel):
    """Request to schedule multiple publications."""

    publications: list["PublicationItem"] = Field(..., min_length=1, max_length=50)


class PublicationItem(BaseModel):
    """Single publication item for bulk scheduling."""

    content_id: UUID
    platform: str = Field(..., pattern="^(youtube|vk|tiktok)$")
    account_id: UUID
    scheduled_at: datetime
    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=5000)

    @field_validator("scheduled_at")
    @classmethod
    def validate_scheduled_time(cls, v: datetime) -> datetime:
        """Allow now or past for immediate publish; future for scheduled."""
        if v.tzinfo is None:
            v = v.replace(tzinfo=UTC)
        return v


class BulkPublishResponse(BaseModel):
    """Response for bulk publication scheduling."""

    created_count: int
    publications: list[PublishResponse]


class PublicationListResponse(BaseModel):
    """Response for publication list with pagination."""

    total: int
    items: list[PublishResponse]
    limit: int
    offset: int
