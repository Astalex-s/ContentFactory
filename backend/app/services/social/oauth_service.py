"""OAuth service for social platform connection."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import logging
import os
import secrets
import time
import uuid
from datetime import UTC, datetime, timedelta
from urllib.parse import urlencode

import httpx
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.encryption import decrypt_token, encrypt_token
from app.models.social_account import SocialAccount, SocialPlatform
from app.repositories.social_account import SocialAccountRepository

log = logging.getLogger(__name__)

os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

YOUTUBE_SCOPE = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
VK_SCOPE = "vkid.personal_info"
TIKTOK_SCOPE = "user.info.basic,video.list,video.upload"

# ---------------------------------------------------------------------------
# PKCE helpers (in-memory store, sufficient for single-instance MVP)
# ---------------------------------------------------------------------------
_PKCE_TTL = 600  # 10 minutes
_pkce_store: dict[str, tuple[str, float]] = {}


def _generate_pkce() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for PKCE S256.
    VK ID requires: code_verifier 43-128 chars [a-zA-Z0-9_-], state >= 32 chars."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


def _store_pkce(state: str, code_verifier: str) -> None:
    now = time.time()
    expired = [k for k, (_, ts) in _pkce_store.items() if now - ts > _PKCE_TTL]
    for k in expired:
        del _pkce_store[k]
    _pkce_store[state] = (code_verifier, now)


def _pop_pkce(state: str) -> str | None:
    entry = _pkce_store.pop(state, None)
    if entry is None:
        return None
    cv, ts = entry
    if time.time() - ts > _PKCE_TTL:
        return None
    return cv


def _get_user_id() -> uuid.UUID:
    """Get user ID. MVP: from DEFAULT_USER_ID env."""
    settings = get_settings()
    uid = settings.DEFAULT_USER_ID
    if not uid:
        raise ValueError("DEFAULT_USER_ID is not set. Configure .env for MVP.")
    try:
        return uuid.UUID(uid)
    except ValueError:
        raise ValueError("DEFAULT_USER_ID must be a valid UUID") from None


def _extract_oauth_app_id_from_state(
    state: str,
) -> tuple[uuid.UUID, str]:  # pyright: ignore[reportUnusedFunction]
    """Extract oauth_app_id from state parameter.
    State format: 'oauth_app_id:random_state'
    Returns: (oauth_app_id, original_state)"""
    if not state or ":" not in state:
        raise ValueError("Invalid state parameter: missing oauth_app_id")
    parts = state.split(":", 1)
    try:
        oauth_app_id = uuid.UUID(parts[0])
        original_state = parts[1]
        return oauth_app_id, original_state
    except (ValueError, IndexError):
        raise ValueError("Invalid state parameter: cannot parse oauth_app_id") from None


class OAuthService:
    """OAuth 2.0 Authorization Code Flow for social platforms."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SocialAccountRepository(session)
        self.settings = get_settings()

    def get_user_id(self) -> uuid.UUID:
        """Get current user ID (MVP: DEFAULT_USER_ID)."""
        return _get_user_id()

    async def get_auth_url(
        self, platform: SocialPlatform, oauth_app_id: uuid.UUID, state: str | None = None
    ) -> str:
        """Generate OAuth authorization URL for platform. Requires oauth_app_id from DB.
        Encodes oauth_app_id in state parameter for callback retrieval."""
        from app.repositories.oauth_app_credentials import OAuthAppCredentialsRepository
        from app.services.social.oauth_app_credentials_service import OAuthAppCredentialsService

        creds_service = OAuthAppCredentialsService(OAuthAppCredentialsRepository(self.session))
        creds = await creds_service.get_credentials_decrypted(oauth_app_id)
        if not creds:
            raise ValueError(f"OAuth app credentials {oauth_app_id} not found or decryption failed")

        client_id, client_secret, redirect_uri = creds

        # Encode oauth_app_id in state parameter: "oauth_app_id:random_state"
        random_state = state or secrets.token_urlsafe(32)
        encoded_state = f"{oauth_app_id}:{random_state}"

        if platform == SocialPlatform.YOUTUBE:
            return self._youtube_auth_url(client_id, client_secret, redirect_uri, encoded_state)
        if platform == SocialPlatform.VK:
            return self._vk_auth_url(client_id, redirect_uri, encoded_state)
        if platform == SocialPlatform.TIKTOK:
            return self._tiktok_auth_url(client_id, redirect_uri, encoded_state)
        raise ValueError(f"Unsupported platform: {platform}")

    def _youtube_auth_url(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None,
        state: str | None = None,
    ) -> str:
        """YouTube OAuth URL from DB credentials."""
        redirect_uri = (
            redirect_uri or f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/youtube"
        )
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        }
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

    def _vk_auth_url(
        self, client_id: str, redirect_uri: str | None, state: str | None = None
    ) -> str:
        """VK ID OAuth 2.1 с PKCE from DB credentials.
        Note: state should already contain oauth_app_id from get_auth_url."""
        if not state:
            state = secrets.token_urlsafe(32)
        code_verifier, code_challenge = _generate_pkce()
        _store_pkce(state, code_verifier)

        redirect_uri = (
            redirect_uri or f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/vk"
        )
        params = {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": "s256",
            "state": state,
            "scope": VK_SCOPE,
        }
        return f"https://id.vk.com/authorize?{urlencode(params)}"

    def _tiktok_auth_url(
        self, client_key: str, redirect_uri: str | None, state: str | None = None
    ) -> str:
        """TikTok OAuth URL from DB credentials."""
        redirect_uri = (
            redirect_uri or f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/tiktok"
        )
        params = {
            "client_key": client_key,
            "response_type": "code",
            "scope": TIKTOK_SCOPE,
            "redirect_uri": redirect_uri,
            "state": state or secrets.token_urlsafe(16),
        }
        return f"https://www.tiktok.com/v2/auth/authorize/?{urlencode(params)}"

    async def exchange_code(
        self,
        platform: SocialPlatform,
        code: str,
        oauth_app_id: uuid.UUID,
        state: str | None = None,
        device_id: str | None = None,
    ) -> SocialAccount:
        """Exchange authorization code for tokens and save account. Requires oauth_app_id from DB."""
        from app.repositories.oauth_app_credentials import OAuthAppCredentialsRepository
        from app.services.social.oauth_app_credentials_service import OAuthAppCredentialsService

        creds_service = OAuthAppCredentialsService(OAuthAppCredentialsRepository(self.session))
        creds = await creds_service.get_credentials_decrypted(oauth_app_id)
        if not creds:
            raise ValueError(f"OAuth app credentials {oauth_app_id} not found or decryption failed")

        client_id, client_secret, redirect_uri = creds
        user_id = _get_user_id()

        if platform == SocialPlatform.YOUTUBE:
            return await self._exchange_youtube(
                code, user_id, client_id, client_secret, redirect_uri, oauth_app_id
            )
        if platform == SocialPlatform.VK:
            return await self._exchange_vk(
                code,
                user_id,
                client_id,
                redirect_uri,
                oauth_app_id,
                state=state,
                device_id=device_id,
            )
        if platform == SocialPlatform.TIKTOK:
            return await self._exchange_tiktok(
                code,
                user_id,
                client_key=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                oauth_app_id=oauth_app_id,
            )
        raise ValueError(f"Unsupported platform: {platform}")

    async def _exchange_youtube(
        self,
        code: str,
        user_id: uuid.UUID,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None,
        oauth_app_id: uuid.UUID,
    ) -> SocialAccount:
        """Exchange YouTube code for tokens and fetch channel info."""
        redirect_uri = (
            redirect_uri or f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/youtube"
        )
        client_config = {
            "web": {
                "client_id": client_id,
                "client_secret": client_secret,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [redirect_uri],
            }
        }
        flow = Flow.from_client_config(
            client_config,
            scopes=YOUTUBE_SCOPE,
            redirect_uri=redirect_uri,
        )
        await asyncio.to_thread(flow.fetch_token, code=code)
        creds = flow.credentials

        expires_at = None
        if creds.expiry:
            expires_at = creds.expiry

        enc_access = encrypt_token(
            creds.token or "", self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT
        )
        enc_refresh = encrypt_token(
            creds.refresh_token or "",
            self.settings.OAUTH_SECRET_KEY,
            self.settings.OAUTH_ENCRYPTION_SALT,
        )

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
                log.warning(
                    "YouTube channels.list failed: %s %s", resp.status_code, resp.text[:200]
                )

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
            oauth_app_credentials_id=oauth_app_id,
        )

    async def _exchange_vk(
        self,
        code: str,
        user_id: uuid.UUID,
        client_id: str,
        redirect_uri: str | None,
        oauth_app_id: uuid.UUID,
        *,
        state: str | None = None,
        device_id: str | None = None,
    ) -> SocialAccount:
        """Exchange VK ID authorization code for tokens (OAuth 2.1 + PKCE)."""
        code_verifier = _pop_pkce(state) if state else None
        if not code_verifier:
            raise ValueError("VK PKCE: state не найден или истёк. Повторите авторизацию.")

        redirect_uri = (
            redirect_uri or f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/vk"
        )
        payload = {
            "grant_type": "authorization_code",
            "code_verifier": code_verifier,
            "redirect_uri": redirect_uri,
            "code": code,
            "client_id": client_id,
            "device_id": device_id or secrets.token_urlsafe(16),
            "state": state,
        }
        async with httpx.AsyncClient(timeout=self.settings.SOCIAL_TIMEOUT) as client:
            resp = await client.post(
                "https://id.vk.com/oauth2/auth",
                data=payload,
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        data = resp.json()
        if "error" in data:
            err_desc = data.get("error_description", data.get("error", "VK token exchange failed"))
            log.warning("VK ID token exchange error: %s", err_desc)
            raise ValueError(err_desc)

        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("VK ID did not return access_token")

        expires_in = data.get("expires_in", 0)
        expires_at = None
        if expires_in > 0:
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        enc_access = encrypt_token(
            access_token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT
        )
        enc_refresh = encrypt_token(
            data.get("refresh_token", ""),
            self.settings.OAUTH_SECRET_KEY,
            self.settings.OAUTH_ENCRYPTION_SALT,
        )
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
            oauth_app_credentials_id=oauth_app_id,
        )

    async def _exchange_tiktok(
        self,
        code: str,
        user_id: uuid.UUID,
        client_key: str,
        client_secret: str,
        redirect_uri: str | None,
        oauth_app_id: uuid.UUID,
    ) -> SocialAccount:
        """Exchange TikTok authorization code for tokens."""
        redirect_uri = (
            redirect_uri or f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/tiktok"
        )
        async with httpx.AsyncClient(timeout=self.settings.SOCIAL_TIMEOUT) as client:
            resp = await client.post(
                "https://open.tiktokapis.com/v2/oauth/token/",
                data={
                    "client_key": client_key,
                    "client_secret": client_secret,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if resp.status_code != 200:
            log.warning("TikTok token exchange error: %s", resp.text)
            raise ValueError("TikTok token exchange failed")

        data = resp.json()
        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("TikTok did not return access_token")

        expires_in = data.get("expires_in", 0)
        expires_at = None
        if expires_in > 0:
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)

        enc_access = encrypt_token(
            access_token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT
        )
        enc_refresh = encrypt_token(
            data.get("refresh_token", ""),
            self.settings.OAUTH_SECRET_KEY,
            self.settings.OAUTH_ENCRYPTION_SALT,
        )
        enc_refresh = enc_refresh or None

        existing = await self.repo.get_by_user_and_platform(user_id, SocialPlatform.TIKTOK)
        if existing:
            await self.repo.update_tokens(existing.id, enc_access, enc_refresh, expires_at)
            return existing

        return await self.repo.create(
            user_id=user_id,
            platform=SocialPlatform.TIKTOK,
            access_token=enc_access,
            refresh_token=enc_refresh,
            expires_at=expires_at,
            oauth_app_credentials_id=oauth_app_id,
        )

    async def refresh_token(self, account_id: uuid.UUID) -> SocialAccount:
        """Refresh access token for account."""
        acc = await self.repo.get_by_id(account_id)
        if not acc:
            raise ValueError("Account not found")
        if not acc.refresh_token:
            raise ValueError("No refresh token")

        dec_refresh = decrypt_token(
            acc.refresh_token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT
        )
        if not dec_refresh:
            raise ValueError("Failed to decrypt refresh token")

        if acc.platform == SocialPlatform.YOUTUBE:
            return await self._refresh_youtube(acc, dec_refresh)
        if acc.platform == SocialPlatform.VK:
            return await self._refresh_vk(acc, dec_refresh)
        if acc.platform == SocialPlatform.TIKTOK:
            return await self._refresh_tiktok(acc, dec_refresh)
        raise ValueError(f"Unsupported platform: {acc.platform}")

    async def _refresh_youtube(self, acc: SocialAccount, refresh_token: str) -> SocialAccount:
        """Refresh YouTube token."""
        import google.auth.transport.requests
        from google.oauth2.credentials import Credentials

        from app.repositories.oauth_app_credentials import OAuthAppCredentialsRepository
        from app.services.social.oauth_app_credentials_service import OAuthAppCredentialsService

        if not acc.oauth_app_credentials_id:
            raise ValueError("No oauth_app_credentials_id for account; cannot refresh token")

        creds_service = OAuthAppCredentialsService(OAuthAppCredentialsRepository(self.session))
        creds_data = await creds_service.get_credentials_decrypted(acc.oauth_app_credentials_id)
        if not creds_data:
            raise ValueError("OAuth app credentials not found or decryption failed")

        client_id, client_secret, _ = creds_data

        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
        )
        creds.refresh(google.auth.transport.requests.Request())

        enc_access = encrypt_token(
            creds.token or "", self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT
        )
        enc_refresh = encrypt_token(
            creds.refresh_token or refresh_token,
            self.settings.OAUTH_SECRET_KEY,
            self.settings.OAUTH_ENCRYPTION_SALT,
        )
        updated = await self.repo.update_tokens(
            acc.id,
            enc_access,
            enc_refresh,
            creds.expiry,
        )
        return updated or acc

    async def _refresh_vk(self, acc: SocialAccount, refresh_token: str) -> SocialAccount:
        """Refresh VK ID token."""
        from app.repositories.oauth_app_credentials import OAuthAppCredentialsRepository
        from app.services.social.oauth_app_credentials_service import OAuthAppCredentialsService

        if not acc.oauth_app_credentials_id:
            raise ValueError("No oauth_app_credentials_id for account; cannot refresh token")

        creds_service = OAuthAppCredentialsService(OAuthAppCredentialsRepository(self.session))
        creds_data = await creds_service.get_credentials_decrypted(acc.oauth_app_credentials_id)
        if not creds_data:
            raise ValueError("OAuth app credentials not found or decryption failed")

        client_id, _, _ = creds_data

        async with httpx.AsyncClient(timeout=self.settings.SOCIAL_TIMEOUT) as client:
            resp = await client.post(
                "https://id.vk.com/oauth2/auth",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": client_id,
                    "device_id": secrets.token_urlsafe(16),
                    "state": secrets.token_urlsafe(32),
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        data = resp.json()
        if "error" in data:
            raise ValueError(data.get("error_description", "VK ID token refresh failed"))
        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("VK ID did not return access_token")
        expires_in = data.get("expires_in", 0)
        expires_at = None
        if expires_in > 0:
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        enc_access = encrypt_token(
            access_token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT
        )
        new_refresh = data.get("refresh_token")
        enc_refresh = (
            encrypt_token(
                new_refresh, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT
            )
            if new_refresh
            else None
        )
        updated = await self.repo.update_tokens(acc.id, enc_access, enc_refresh, expires_at)
        return updated or acc

    async def _refresh_tiktok(self, acc: SocialAccount, refresh_token: str) -> SocialAccount:
        """Refresh TikTok token."""
        from app.repositories.oauth_app_credentials import OAuthAppCredentialsRepository
        from app.services.social.oauth_app_credentials_service import OAuthAppCredentialsService

        if not acc.oauth_app_credentials_id:
            raise ValueError("No oauth_app_credentials_id for account; cannot refresh token")

        creds_service = OAuthAppCredentialsService(OAuthAppCredentialsRepository(self.session))
        creds_data = await creds_service.get_credentials_decrypted(acc.oauth_app_credentials_id)
        if not creds_data:
            raise ValueError("OAuth app credentials not found or decryption failed")

        client_id, client_secret, _ = creds_data

        async with httpx.AsyncClient(timeout=self.settings.SOCIAL_TIMEOUT) as client:
            resp = await client.post(
                "https://open.tiktokapis.com/v2/oauth/token/",
                data={
                    "client_key": client_id,
                    "client_secret": client_secret,
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        if resp.status_code != 200:
            raise ValueError("TikTok token refresh failed")
        data = resp.json()
        access_token = data.get("access_token")
        if not access_token:
            raise ValueError("TikTok did not return access_token")
        expires_in = data.get("expires_in", 0)
        expires_at = None
        if expires_in > 0:
            expires_at = datetime.now(UTC) + timedelta(seconds=expires_in)
        enc_access = encrypt_token(
            access_token, self.settings.OAUTH_SECRET_KEY, self.settings.OAUTH_ENCRYPTION_SALT
        )
        enc_refresh = encrypt_token(
            data.get("refresh_token", refresh_token),
            self.settings.OAUTH_SECRET_KEY,
            self.settings.OAUTH_ENCRYPTION_SALT,
        )
        updated = await self.repo.update_tokens(acc.id, enc_access, enc_refresh, expires_at)
        return updated or acc
