"""OAuth service for social platform connection."""

from __future__ import annotations

import asyncio
import base64
import hashlib
import json
import logging
import os
import secrets
import uuid
from datetime import UTC, datetime, timedelta
import httpx
from google_auth_oauthlib.flow import Flow
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.encryption import decrypt_token, encrypt_token
from app.models.social_account import SocialAccount, SocialPlatform
from app.repositories.oauth_pkce import OAuthPkceRepository
from app.repositories.social_account import SocialAccountRepository

log = logging.getLogger(__name__)

os.environ.setdefault("OAUTHLIB_RELAX_TOKEN_SCOPE", "1")

YOUTUBE_SCOPE = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/userinfo.email",
    "https://www.googleapis.com/auth/userinfo.profile",
]
_PKCE_TTL_SECONDS = 600  # 10 minutes


def _generate_pkce() -> tuple[str, str]:
    """Return (code_verifier, code_challenge) for PKCE S256."""
    code_verifier = secrets.token_urlsafe(64)
    digest = hashlib.sha256(code_verifier.encode("ascii")).digest()
    code_challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return code_verifier, code_challenge


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


def _extract_oauth_app_id_from_state(  # pyright: ignore
    state: str,
) -> tuple[uuid.UUID, str]:
    """Extract oauth_app_id from state parameter.
    Supports: JSON {oauth_app_id: "..."}, or format oauth_app_id:random_state.
    Returns: (oauth_app_id, original_state)"""
    if not state or not state.strip():
        log.warning("_extract_oauth_app_id_from_state: state пустой")
        raise ValueError("Invalid state parameter: missing oauth_app_id")
    state = state.strip()

    # JSON format: {"oauth_app_id": "uuid", ...}
    if state.startswith("{"):
        try:
            data = json.loads(state)
            oauth_app_id_str = data.get("oauth_app_id")
            if oauth_app_id_str:
                oauth_app_id = uuid.UUID(str(oauth_app_id_str))
                return oauth_app_id, state
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            log.warning("_extract_oauth_app_id_from_state: JSON parse failed: %s", e)

    # Standard format: oauth_app_id:random_state
    if ":" in state:
        parts = state.split(":", 1)
        try:
            oauth_app_id = uuid.UUID(parts[0])
            original_state = parts[1]
            return oauth_app_id, original_state
        except (ValueError, IndexError):
            pass

    log.warning(
        "_extract_oauth_app_id_from_state: state не распознан len=%d has_colon=%s preview=%s",
        len(state),
        ":" in state,
        state[:50] + "..." if len(state) > 50 else state,
    )
    raise ValueError("Invalid state parameter: missing oauth_app_id")


class OAuthService:
    """OAuth 2.0 Authorization Code Flow for social platforms."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = SocialAccountRepository(session)
        self.pkce_repo = OAuthPkceRepository(session)
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
            return await self._youtube_auth_url(
                client_id, client_secret, redirect_uri, encoded_state
            )
        raise ValueError("Поддерживается только YouTube")

    async def _youtube_auth_url(
        self,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None,
        state: str | None = None,
    ) -> str:
        """YouTube OAuth URL from DB credentials. Uses PKCE (code_challenge)."""
        redirect_uri = (
            redirect_uri or f"{self.settings.API_BASE_URL.rstrip('/')}/social/callback/youtube"
        )
        state_val = state or secrets.token_urlsafe(32)
        code_verifier, _ = _generate_pkce()
        expires_at = datetime.now(UTC) + timedelta(seconds=_PKCE_TTL_SECONDS)
        await self.pkce_repo.store(state_val, code_verifier, expires_at)
        await self.session.commit()
        log.debug(
            "YouTube PKCE stored state (len=%d), expires_at=%s",
            len(state_val),
            expires_at,
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
            code_verifier=code_verifier,
            autogenerate_code_verifier=False,
        )
        auth_url, _ = flow.authorization_url(
            access_type="offline",
            prompt="consent",
            include_granted_scopes="true",
            state=state_val,
        )
        return auth_url

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
                code,
                user_id,
                client_id,
                client_secret,
                redirect_uri,
                oauth_app_id,
                state=state,
            )
        raise ValueError("Поддерживается только YouTube")

    async def _exchange_youtube(
        self,
        code: str,
        user_id: uuid.UUID,
        client_id: str,
        client_secret: str,
        redirect_uri: str | None,
        oauth_app_id: uuid.UUID,
        *,
        state: str | None = None,
    ) -> SocialAccount:
        """Exchange YouTube code for tokens and fetch channel info. Uses PKCE code_verifier."""
        code_verifier = await self.pkce_repo.pop(state) if state else None
        if not code_verifier:
            log.warning(
                "YouTube PKCE: state не найден (state=%s, len=%d). Проверьте: один backend, commit после store.",
                state[:50] + "..." if state and len(state) > 50 else (state or "(empty)"),
                len(state) if state else 0,
            )
            raise ValueError("YouTube PKCE: state не найден или истёк. Повторите авторизацию.")

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
        await asyncio.to_thread(flow.fetch_token, code=code, code_verifier=code_verifier)
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
        raise ValueError("Поддерживается только YouTube")

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
