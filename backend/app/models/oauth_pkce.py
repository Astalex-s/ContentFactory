"""OAuth PKCE state model for storing code_verifier during OAuth flow."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class OAuthPkceState(Base):
    """Temporary PKCE code_verifier storage. Keyed by state, expires after TTL."""

    __tablename__ = "oauth_pkce_state"

    state: Mapped[str] = mapped_column(
        String(512),
        primary_key=True,
        comment="OAuth state (oauth_app_id:random_state)",
    )
    code_verifier: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        comment="Expiry time, typically 10 min from creation",
    )
