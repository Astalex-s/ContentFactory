"""Social account model for OAuth-connected platforms."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SocialPlatform(str, enum.Enum):
    """Supported social platforms."""

    YOUTUBE = "youtube"
    VK = "vk"
    TIKTOK = "tiktok"


class SocialAccount(Base):
    """OAuth-connected social account. Tokens stored encrypted."""

    __tablename__ = "social_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        nullable=False,
        index=True,
    )
    platform: Mapped[SocialPlatform] = mapped_column(
        Enum(SocialPlatform, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    access_token: Mapped[str] = mapped_column(Text, nullable=False)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    channel_id: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    channel_title: Mapped[str | None] = mapped_column(String(256), nullable=True)
    oauth_app_credentials_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="FK to oauth_app_credentials used for this account",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
