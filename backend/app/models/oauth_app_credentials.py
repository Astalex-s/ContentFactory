"""OAuth application credentials model for storing custom OAuth apps."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.social_account import SocialPlatform


class OAuthAppCredentials(Base):
    """Custom OAuth application credentials. client_secret stored encrypted."""

    __tablename__ = "oauth_app_credentials"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
        comment="Owner user_id or null for global apps",
    )
    platform: Mapped[SocialPlatform] = mapped_column(
        Enum(SocialPlatform, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(
        String(256),
        nullable=False,
        comment="Display name for this OAuth app",
    )
    client_id: Mapped[str] = mapped_column(String(512), nullable=False)
    client_secret: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        comment="Encrypted client_secret",
    )
    redirect_uri: Mapped[Optional[str]] = mapped_column(
        String(512),
        nullable=True,
        comment="Optional custom redirect_uri",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )
