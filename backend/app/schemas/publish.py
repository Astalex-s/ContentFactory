"""Pydantic schemas for publication."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PublishRequest(BaseModel):
    """Request to schedule publication. content_id from path."""

    platform: str
    account_id: UUID
    scheduled_at: datetime | None = None
    title: str | None = None
    description: str | None = None


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


class PublishStatusResponse(BaseModel):
    """Publication status response."""

    id: UUID
    status: str
    error_message: str | None
    platform_video_id: str | None
