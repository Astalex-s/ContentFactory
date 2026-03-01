"""Social account repository."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.social_account import SocialAccount, SocialPlatform


class SocialAccountRepository:
    """Repository for SocialAccount CRUD."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        user_id: UUID,
        platform: SocialPlatform,
        access_token: str,
        refresh_token: str | None = None,
        expires_at=None,
        channel_id: str | None = None,
        channel_title: str | None = None,
        oauth_app_credentials_id: UUID | None = None,
    ) -> SocialAccount:
        """Create social account."""
        acc = SocialAccount(
            user_id=user_id,
            platform=platform,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at,
            channel_id=channel_id,
            channel_title=channel_title,
            oauth_app_credentials_id=oauth_app_credentials_id,
        )
        self.session.add(acc)
        await self.session.flush()
        await self.session.refresh(acc)
        return acc

    async def get_by_id(self, account_id: UUID) -> SocialAccount | None:
        """Get account by ID."""
        result = await self.session.execute(
            select(SocialAccount).where(SocialAccount.id == account_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_and_platform(
        self,
        user_id: UUID,
        platform: SocialPlatform,
    ) -> SocialAccount | None:
        """Get account by user and platform."""
        result = await self.session.execute(
            select(SocialAccount)
            .where(SocialAccount.user_id == user_id)
            .where(SocialAccount.platform == platform)
        )
        return result.scalar_one_or_none()

    async def list_by_user(self, user_id: UUID) -> list[SocialAccount]:
        """List all accounts for user."""
        result = await self.session.execute(
            select(SocialAccount)
            .where(SocialAccount.user_id == user_id)
            .order_by(SocialAccount.platform)
        )
        return list(result.scalars().all())

    async def list_by_platform(self, platform: str | SocialPlatform) -> list[SocialAccount]:
        """List accounts for platform (any user)."""
        p = SocialPlatform(platform) if isinstance(platform, str) else platform
        result = await self.session.execute(
            select(SocialAccount)
            .where(SocialAccount.platform == p)
            .order_by(SocialAccount.channel_title)
        )
        return list(result.scalars().all())

    async def update_tokens(
        self,
        account_id: UUID,
        access_token: str,
        refresh_token: str | None = None,
        expires_at=None,
        channel_id: str | None = None,
        channel_title: str | None = None,
    ) -> SocialAccount | None:
        """Update tokens and optionally channel info for account."""
        acc = await self.get_by_id(account_id)
        if acc is None:
            return None
        acc.access_token = access_token
        if refresh_token is not None:
            acc.refresh_token = refresh_token
        if expires_at is not None:
            acc.expires_at = expires_at
        if channel_id is not None:
            acc.channel_id = channel_id
        if channel_title is not None:
            acc.channel_title = channel_title
        await self.session.flush()
        await self.session.refresh(acc)
        return acc

    async def get_by_user_platform_channel(
        self,
        user_id: UUID,
        platform: SocialPlatform,
        channel_id: str | None,
    ) -> SocialAccount | None:
        """Get account by user, platform and channel_id. For YouTube multi-channel."""
        if channel_id:
            result = await self.session.execute(
                select(SocialAccount)
                .where(SocialAccount.user_id == user_id)
                .where(SocialAccount.platform == platform)
                .where(SocialAccount.channel_id == channel_id)
            )
            return result.scalar_one_or_none()
        return await self.get_by_user_and_platform(user_id, platform)

    async def update_channel_title(
        self, account_id: UUID, channel_title: str | None
    ) -> SocialAccount | None:
        """Update channel display title."""
        acc = await self.get_by_id(account_id)
        if acc is None:
            return None
        acc.channel_title = channel_title or None
        await self.session.flush()
        await self.session.refresh(acc)
        return acc

    async def delete(self, account_id: UUID) -> bool:
        """Delete account by ID."""
        acc = await self.get_by_id(account_id)
        if acc is None:
            return False
        await self.session.delete(acc)
        await self.session.flush()
        return True
