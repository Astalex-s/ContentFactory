"""Generated content model."""

from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ContentType(str, enum.Enum):
    """Content type enum."""

    TEXT = "text"
    IMAGE = "image"
    VIDEO = "video"


class ContentStatus(str, enum.Enum):
    """Content status enum."""

    DRAFT = "draft"
    READY = "ready"
    PUBLISHED = "published"


class Platform(str, enum.Enum):
    """Target platform enum."""

    YOUTUBE = "youtube"
    VK = "vk"
    TIKTOK = "tiktok"


class Tone(str, enum.Enum):
    """Content tone enum."""

    NEUTRAL = "neutral"
    EMOTIONAL = "emotional"
    EXPERT = "expert"


class ContentTextType(str, enum.Enum):
    """Type of generated text content."""

    SHORT_POST = "short_post"
    VIDEO_DESCRIPTION = "video_description"
    CTA = "cta"
    ALL = "all"


class GeneratedContent(Base):
    """Generated content entity."""

    __tablename__ = "generated_content"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    content_type: Mapped[ContentType] = mapped_column(
        Enum(ContentType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ContentType.TEXT,
    )
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str | None] = mapped_column(String(512), nullable=True)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ContentStatus.DRAFT,
    )
    content_variant: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    platform: Mapped[Platform] = mapped_column(
        Enum(Platform, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    tone: Mapped[Tone] = mapped_column(
        Enum(Tone, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
    )
    content_text_type: Mapped[ContentTextType] = mapped_column(
        Enum(ContentTextType, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        default=ContentTextType.SHORT_POST,
    )
    ai_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    approved_for_publication: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="false"
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
