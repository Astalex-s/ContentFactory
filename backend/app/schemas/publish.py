"""Pydantic schemas for publication."""

from datetime import UTC, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


def _validate_uuid(v: str | UUID, field_name: str) -> UUID:
    """Validate and parse UUID. Reject common invalid values."""
    if isinstance(v, UUID):
        return v
    if v is None:
        raise ValueError(f"{field_name}: ожидается UUID")
    s = str(v).strip().lower()
    if not s or s in ("undefined", "null"):
        raise ValueError(f"{field_name}: неверный формат (получено: {s!r})")
    try:
        return UUID(s)
    except (ValueError, TypeError) as e:
        raise ValueError(f"{field_name}: неверный UUID") from e


class PublishRequest(BaseModel):
    """Request to schedule publication. content_id from path."""

    platform: str = Field(..., pattern="^youtube$")
    account_id: UUID

    @model_validator(mode="before")
    @classmethod
    def normalize_platform(cls, data: dict) -> dict:
        """Normalize platform to lowercase."""
        if isinstance(data, dict) and "platform" in data and data["platform"]:
            data = {**data, "platform": str(data["platform"]).strip().lower()}
        return data

    scheduled_at: datetime | None = None
    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=5000)
    privacy_status: str = Field(
        default="private",
        pattern="^(private|public|unlisted)$",
        description="YouTube: private, public, unlisted",
    )

    @field_validator("account_id", mode="before")
    @classmethod
    def validate_account_id(cls, v: str | UUID) -> UUID:
        return _validate_uuid(v, "account_id")

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
    privacy_status: str | None = None
    views: int | None = None


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
    platform: str = Field(..., pattern="^youtube$")
    account_id: UUID
    scheduled_at: datetime
    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=5000)
    privacy_status: str = Field(
        default="private",
        pattern="^(private|public|unlisted)$",
        description="YouTube: private, public, unlisted",
    )

    @model_validator(mode="before")
    @classmethod
    def sanitize_invalid_strings(cls, data: dict) -> dict:
        """Normalize platform to lowercase; reject invalid content_id/account_id."""
        if not isinstance(data, dict):
            return data
        data = dict(data)
        if "platform" in data and data["platform"]:
            data["platform"] = str(data["platform"]).strip().lower()
        for key in ("content_id", "account_id"):
            val = data.get(key)
            if val is None:
                raise ValueError(f"{key}: обязательно для заполнения")
            s = str(val).strip().lower()
            if not s or s in ("undefined", "null"):
                raise ValueError(f"{key}: неверный формат (получено: {s!r})")
        return data

    @field_validator("content_id", "account_id", mode="before")
    @classmethod
    def validate_uuid_fields(cls, v: str) -> UUID:
        return _validate_uuid(v, "ID")

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
