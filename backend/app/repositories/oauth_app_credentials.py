"""Repository for OAuth app credentials."""

from __future__ import annotations

import uuid

from sqlalchemy import select

_UNSET = object()
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oauth_app_credentials import OAuthAppCredentials
from app.models.social_account import SocialPlatform


class OAuthAppCredentialsRepository:
    """Repository for CRUD operations on oauth_app_credentials."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create(
        self,
        user_id: uuid.UUID | None,
        platform: SocialPlatform,
        name: str,
        client_id: str,
        client_secret_encrypted: str,
        redirect_uri: str | None = None,
    ) -> OAuthAppCredentials:
        """Create new OAuth app credentials."""
        app = OAuthAppCredentials(
            user_id=user_id,
            platform=platform,
            name=name,
            client_id=client_id,
            client_secret=client_secret_encrypted,
            redirect_uri=redirect_uri,
        )
        self.session.add(app)
        await self.session.flush()
        await self.session.refresh(app)
        return app

    async def get_by_id(self, app_id: uuid.UUID) -> OAuthAppCredentials | None:
        """Get OAuth app by ID."""
        stmt = select(OAuthAppCredentials).where(OAuthAppCredentials.id == app_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_platform(
        self, platform: SocialPlatform | None = None, user_id: uuid.UUID | None = None
    ) -> list[OAuthAppCredentials]:
        """List OAuth apps, optionally filtered by platform and/or user_id."""
        stmt = select(OAuthAppCredentials)
        if platform:
            stmt = stmt.where(OAuthAppCredentials.platform == platform)
        if user_id is not None:
            stmt = stmt.where(OAuthAppCredentials.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all(self, user_id: uuid.UUID | None = None) -> list[OAuthAppCredentials]:
        """List all OAuth apps for user."""
        stmt = select(OAuthAppCredentials)
        if user_id is not None:
            stmt = stmt.where(OAuthAppCredentials.user_id == user_id)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def update(
        self,
        app_id: uuid.UUID,
        name: str | None = _UNSET,
        client_id: str | None = _UNSET,
        client_secret_encrypted: str | None = _UNSET,
        redirect_uri: str | None = _UNSET,
    ) -> OAuthAppCredentials | None:
        """Update OAuth app credentials (partial). Use None for redirect_uri to clear it."""
        app = await self.get_by_id(app_id)
        if not app:
            return None
        if name is not _UNSET:
            app.name = name
        if client_id is not _UNSET:
            app.client_id = client_id
        if client_secret_encrypted is not _UNSET:
            app.client_secret = client_secret_encrypted
        if redirect_uri is not _UNSET:
            app.redirect_uri = redirect_uri
        await self.session.flush()
        await self.session.refresh(app)
        return app

    async def delete(self, app_id: uuid.UUID) -> bool:
        """Delete OAuth app credentials. Returns True if deleted."""
        app = await self.get_by_id(app_id)
        if not app:
            return False
        await self.session.delete(app)
        await self.session.flush()
        return True
