"""Pydantic schemas for social OAuth and accounts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class SocialAccountRead(BaseModel):
    """Social account response."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    platform: str
    created_at: datetime


class ConnectResponse(BaseModel):
    """OAuth connect response - redirect URL."""

    auth_url: str


class CallbackSuccess(BaseModel):
    """OAuth callback success."""

    message: str = "Аккаунт успешно подключён"
    account_id: UUID


class SocialAccountResponse(BaseModel):
    """Single social account in list."""

    id: UUID
    platform: str
    channel_id: str | None = None
    channel_title: str | None = None
    created_at: str | None


class SocialAccountsListResponse(BaseModel):
    """List of social accounts."""

    accounts: list[SocialAccountResponse]


class SocialAccountUpdate(BaseModel):
    """Update social account (display name)."""

    channel_title: str | None = Field(
        None, max_length=256, description="Отображаемое название канала"
    )


# OAuth App Credentials schemas


class OAuthAppCreate(BaseModel):
    """Create OAuth app credentials."""

    platform: str = Field(..., pattern="^(youtube|vk)$", description="Platform: youtube, vk")
    name: str = Field(..., min_length=1, max_length=256, description="Display name")
    client_id: str = Field(..., min_length=1, max_length=512)
    client_secret: str = Field(..., min_length=1, description="Will be encrypted")
    redirect_uri: str | None = Field(None, max_length=512)


class OAuthAppUpdate(BaseModel):
    """Update OAuth app credentials (partial)."""

    name: str | None = Field(None, min_length=1, max_length=256)
    client_id: str | None = Field(None, min_length=1, max_length=512)
    client_secret: str | None = Field(None, min_length=1, description="Will be encrypted")
    redirect_uri: str | None = Field(None, max_length=512)


class OAuthAppRead(BaseModel):
    """OAuth app credentials response (without client_secret)."""

    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: UUID | None
    platform: str
    name: str
    client_id_masked: str = Field(..., description="Masked client_id (last 4 chars)")
    redirect_uri: str | None
    created_at: datetime
    updated_at: datetime


class OAuthAppListResponse(BaseModel):
    """List of OAuth app credentials."""

    apps: list[OAuthAppRead]
