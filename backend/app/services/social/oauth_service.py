"""OAuth service for social platform connection."""

from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional
from urllib.parse import urlencode

import httpx
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.encryption import decrypt_token, encrypt_token
from app.models.social_account import SocialAccount, SocialPlatform
from app.repositories.social_account import SocialAccountRepository

log = logging.getLogger(__name__)

# Google returns scopes in different order/adds openid — oauthlib raises ScopeChangeWarning.
# Relax validation to avoid 500 on callback.
os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

# YouTube OAuth scope for upload
YOUTUBE_SCOPE = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
VK_SCOPE = "video"
RUTUBE_SCOPE = "video"


def _get_user_id() -> uuid.UUID:
    """Get user ID. MVP: from DEFAULT_USER_ID env."""
    settings = get_settings()
    uid = settings.DEFAULT_USER_ID
    if not uid:
        raise ValueError("DEFAULT_USER_ID is not set. Configure .env for MVP.")
    try:
        return uuid.UUID(uid)
    except ValueError:
        raise ValueError("DEFAULT_USER_ID must be a valid UUID")


class OAuthService:
    """OAuth 2.0 Authorization Code Flow for social platforms."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SocialAccountRepository(session)
        self.settings = get_settings()

    def get_user_id(self) -> uuid.UUID:
        """Get current user ID (MVP: DEFAULT_USER_ID)."""
        return _get_user_id()

    def get_auth_url(self, platform: SocialPlatform, state: Optional[str] = None) -> str:
        """Generate OAuth authorization URL for platform."""
        if platform == SocialPlatform.YOUTUBE:
            return self._youtube_auth_url(state)
        if platform == SocialPlatform.VK:
            return self._vk_auth_url(state)
        if platform == SocialPlatform.RUTUBE:
            return self._rutube_auth_url(state)
        raise ValueError(f"Unsupported platform: {platform}")

    def _youtube_auth_url(self, state: Optional[str] = None) -> str:
        """YouTube OAuth URL."""
        client_config = {
            "web": {
                "client_id": self.settings.YOUTUBE_CLIENT_ID,
                "client_secret": self.settings.YOUTUBE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/youtube"],
            }
        }
        redirect_uri = client_config["web"]["redirect_uris"][0]
        flow = Flow.from_client_config(
            client_config,
            scopes=YOUTUBE_SCOPE,
            redirect_uri=redirect_uri,
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
            state=state or "",
        )
        return auth_url

    def _vk_auth_url(self, state: Optional[str] = None) -> str:
        """VK OAuth URL."""
        params = {
            "client_id": self.settings.VK_CLIENT_ID,
            "display": "page",
            "redirect_uri": f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/vk",
            "scope": VK_SCOPE,
            "response_type": "code",
            "v": "5.131",
        }
        if state:
            params["state"] = state
        return f"https://oauth.vk.ru/authorize?{urlencode(params)}"

    def _rutube_auth_url(self, state: Optional[str] = None) -> str:
        """Rutube OAuth URL (placeholder - no official upload API)."""
        params = {
            "client_id": self.settings.RUTUBE_CLIENT_ID,
            "response_type": "code",
            "redirect_uri": f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/rutube",
        }
        if state:
            params["state"] = state
        return f"https://oauth.rutube.ru/oauth2/authorize?{urlencode(params)}"

    async def exchange_code(
        self,
        platform: SocialPlatform,
        code: str,
        state: Optional[str] = None,
    ) -> SocialAccount:
        """Exchange authorization code for tokens and save account."""
        user_id = _get_user_id()
        if platform == SocialPlatform.YOUTUBE:
            return await self._exchange_youtube(code, user_id)
        if platform == SocialPlatform.VK:
            return await self._exchange_vk(code, user_id)
        if platform == SocialPlatform.RUTUBE:
            return await self._exchange_rutube(code, user_id)
        raise ValueError(f"Unsupported platform: {platform}")

    async def _exchange_youtube(self, code: str, user_id: uuid.UUID) -> SocialAccount:
        """Exchange YouTube code for tokens and fetch channel info."""
        client_config = {
            "web": {
                "client_id": self.settings.YOUTUBE_CLIENT_ID,
                "client_secret": self.settings.YOUTUBE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/youtube"],
            }
        }
        redirect_uri = client_config["web"]["redirect_uris"][0]
        flow = Flow.from_client_config(
            client_config,
            scopes=YOUTUBE_SCOPE,
            redirect_uri=redirect_uri,
        )
        # fetch_token is blocking; run in thread pool
        await asyncio.to_thread(flow.fetch_token, code=code)
        creds = flow.credentials

        expires_at = None
        if creds.expiry:
            expires_at = creds.expiry

        enc_access = encrypt_token(creds.token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)
        enc_refresh = encrypt_token(creds.refresh_token or "", self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)

        channel_id: str | None = None
        channel_title: str | None = None
        async with httpx.AsyncClient(timeout=self.settings.SOCIAL_TIMEOUT) as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params={"part": "snippet", "mine": "true"},
                headers={"Authorization": f"Bearer {creds.token}"},
            )
            if resp.status_code == 200:
                data = resp.json()
                items = data.get("items", [])
                if items:
                    channel_id = items[0].get("id")
                    channel_title = items[0].get("snippet", {}).get("title")
            else:
                log.warning("YouTube channels.list failed: %s %s", resp.status_code, resp.text[:200])

        existing = await self.repo.get_by_user_platform_channel(
            user_id, SocialPlatform.YOUTUBE, channel_id
        )
        if existing:
            updated = await self.repo.update_tokens(
                existing.id,
                enc_access,
                enc_refresh or existing.refresh_token,
                expires_at,
                channel_id=channel_id,
                channel_title=channel_title,
            )
            return updated or existing

        return await self.repo.create(
            user_id=user_id,
            platform=SocialPlatform.YOUTUBE,
            access_token=enc_access,
            refresh_token=enc_refresh or None,
            expires_at=expires_at,
            channel_id=channel_id,
            channel_title=channel_title,
        )

    async def _exchange_vk(self, code: str, user_id: uuid.UUID) -> SocialAccount:
        """Exchange VK code for tokens."""
        async with httpx.AsyncClient(timeout=self.settings.SOCIAL_TIMEOUT) as client:
            resp = await client.get(
                "https://oauth.vk.ru/access_token",
                params={
                    "client_id": self.settings.VK_CLIENT_ID,
                    "client_secret": self.settings.VK_CLIENT_SECRET,
                    "redirect_uri": f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/vk",
                    "code": code,
                },
            )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            log.warning("VK token exchange error: %s", data.get("error_description"))
            raise ValueError(data.get("error_description", "VK token exchange failed"))

        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("VK did not return access_token")

        expires_in = data.get("expires_in", 0)
        expires_at = None
        if expires_in > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        enc_access = encrypt_token(access_token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)
        enc_refresh = encrypt_token(data.get("refresh_token", ""), self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)
        enc_refresh = enc_refresh or None

        existing = await self.repo.get_by_user_and_platform(user_id, SocialPlatform.VK)
        if existing:
            await self.repo.update_tokens(existing.id, enc_access, enc_refresh, expires_at)
            return existing

        return await self.repo.create(
            user_id=user_id,
            platform=SocialPlatform.VK,
            access_token=enc_access,
            refresh_token=enc_refresh,
            expires_at=expires_at,
        )

    async def _exchange_rutube(self, code: str, user_id: uuid.UUID) -> SocialAccount:
        """Exchange Rutube code (placeholder - no official upload API)."""
        async with httpx.AsyncClient(timeout=self.settings.SOCIAL_TIMEOUT) as client:
            resp = await client.post(
                "https://oauth.rutube.ru/oauth2/token",
                data={
                    "client_id": self.settings.RUTUBE_CLIENT_ID,
                    "client_secret": self.settings.RUTUBE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/rutube",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if resp.status_code != 200:
            log.warning("Rutube token exchange error: %s", resp.text)
            raise ValueError("Rutube token exchange failed")

        data = resp.json()
        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("Rutube did not return access_token")

        expires_in = data.get("expires_in", 0)
        expires_at = None
        if expires_in > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        enc_access = encrypt_token(access_token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)
        enc_refresh = encrypt_token(data.get("refresh_token", ""), self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)
        enc_refresh = enc_refresh or None

        existing = await self.repo.get_by_user_and_platform(user_id, SocialPlatform.RUTUBE)
        if existing:
            await self.repo.update_tokens(existing.id, enc_access, enc_refresh, expires_at)
            return existing

        return await self.repo.create(
            user_id=user_id,
            platform=SocialPlatform.RUTUBE,
            access_token=enc_access,
            refresh_token=enc_refresh,
            expires_at=expires_at,
        )

    async def refresh_token(self, account_id: uuid.UUID) -> SocialAccount:
        """Refresh access token for account."""
        acc = await self.repo.get_by_id(account_id)
        if not acc:
            raise ValueError("Account not found")
        if not acc.refresh_token:
            raise ValueError("No refresh token")

        dec_refresh = decrypt_token(acc.refresh_token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)
        if not dec_refresh:
            raise ValueError("Failed to decrypt refresh token")

        if acc.platform == SocialPlatform.YOUTUBE:
            return await self._refresh_youtube(acc, dec_refresh)
        if acc.platform == SocialPlatform.VK:
            return await self._refresh_vk(acc, dec_refresh)
        if acc.platform == SocialPlatform.RUTUBE:
            return await self._refresh_rutube(acc, dec_refresh)
        raise ValueError(f"Unsupported platform: {acc.platform}")

    async def _refresh_youtube(self, acc: SocialAccount, refresh_token: str) -> SocialAccount:
        """Refresh YouTube token."""
        import google.auth.transport.requests
        from google.oauth2.credentials import Credentials

        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.settings.YOUTUBE_CLIENT_ID,
            client_secret=self.settings.YOUTUBE_CLIENT_SECRET,
        )
        creds.refresh(google.auth.transport.requests.Request())

        enc_access = encrypt_token(creds.token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)
        enc_refresh = encrypt_token(creds.refresh_token or refresh_token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)
        updated = await self.repo.update_tokens(
            acc.id,
            enc_access,
            enc_refresh,
            creds.expiry,
        )
        return updated or acc

    async def _refresh_vk(self, acc: SocialAccount, refresh_token: str) -> SocialAccount:
        """Refresh VK token (VK tokens may not expire)."""
        async with httpx.AsyncClient(timeout=self.settings.SOCIAL_TIMEOUT) as client:
            resp = await client.get(
                "https://oauth.vk.ru/access_token",
                params={
                    "client_id": self.settings.VK_CLIENT_ID,
                    "client_secret": self.settings.VK_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
        if resp.status_code != 200:
            raise ValueError("VK token refresh failed")
        data = resp.json()
        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("VK did not return access_token")
        expires_in = data.get("expires_in", 0)
        expires_at = None
        if expires_in > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        enc_access = encrypt_token(access_token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)
        updated = await self.repo.update_tokens(acc.id, enc_access, None, expires_at)
        return updated or acc

    async def _refresh_rutube(self, acc: SocialAccount, refresh_token: str) -> SocialAccount:
        """Refresh Rutube token."""
        async with httpx.AsyncClient(timeout=self.settings.SOCIAL_TIMEOUT) as client:
            resp = await client.post(
                "https://oauth.rutube.ru/oauth2/token",
                data={
                    "client_id": self.settings.RUTUBE_CLIENT_ID,
                    "client_secret": self.settings.RUTUBE_CLIENT_SECRET,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if resp.status_code != 200:
            raise ValueError("Rutube token refresh failed")
        data = resp.json()
        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("Rutube did not return access_token")
        expires_in = data.get("expires_in", 0)
        expires_at = None
        if expires_in > 0:
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        enc_access = encrypt_token(access_token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)
        enc_refresh = encrypt_token(data.get("refresh_token", refresh_token), self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT)
        updated = await self.repo.update_tokens(acc.id, enc_access, enc_refresh, expires_at)
        return updated or acc
