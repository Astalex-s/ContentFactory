"""Pydantic schemas for social OAuth and accounts."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
