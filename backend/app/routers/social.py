"""Social OAuth router. No business logic in router."""

from __future__ import annotations

import logging
from urllib.parse import quote
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

from app.core.config import get_settings
from app.dependencies import (
    get_oauth_app_credentials_service,
    get_oauth_service,
    get_social_account_repository,
)
from app.models.social_account import SocialPlatform
from app.repositories.social_account import SocialAccountRepository
from app.schemas.social import (
    OAuthAppCreate,
    OAuthAppListResponse,
    OAuthAppRead,
    OAuthAppUpdate,
    SocialAccountResponse,
    SocialAccountsListResponse,
    SocialAccountUpdate,
)
from app.services.social.oauth_app_credentials_service import OAuthAppCredentialsService
from app.services.social.oauth_service import OAuthService

log = logging.getLogger(__name__)

router = APIRouter(prefix="/social", tags=["social"])


def _parse_platform(platform: str) -> SocialPlatform:
    """Parse platform string to enum. Raises 400 if invalid or unsupported."""
    p = platform.lower()
    if p != "youtube":
        raise HTTPException(status_code=400, detail="Поддерживается только YouTube") from None
    return SocialPlatform.YOUTUBE


@router.get("/connect/{platform}")
async def connect_platform(
    platform: str,
    oauth_app_id: UUID = Query(..., description="OAuth app credentials ID (required)"),
    oauth: OAuthService = Depends(get_oauth_service),
) -> dict:
    """Get OAuth authorization URL. Redirect user to this URL. Requires oauth_app_id."""
    p = _parse_platform(platform)
    try:
        auth_url = await oauth.get_auth_url(p, oauth_app_id=oauth_app_id)
        return {"auth_url": auth_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: str | None = Query(None, description="OAuth state parameter (contains oauth_app_id)"),
    oauth: OAuthService = Depends(get_oauth_service),
) -> RedirectResponse:
    """OAuth callback. Exchange code for tokens, redirect to frontend.
    oauth_app_id is extracted from state parameter."""
    p = _parse_platform(platform)
    frontend_url = get_settings().FRONTEND_URL
    settings = get_settings()
    redirect_uri = f"{settings.API_BASE_URL.rstrip('/')}/social/callback/{platform}"

    if not state:
        log.warning(
            "oauth_callback: state пустой platform=%s redirect_uri=%s",
            platform,
            redirect_uri,
        )
    else:
        log.warning(
            "oauth_callback: state len=%d has_colon=%s preview=%s",
            len(state),
            ":" in state,
            state[:50] + "..." if len(state) > 50 else state,
        )

    try:
        from app.services.social.oauth_service import _extract_oauth_app_id_from_state

        oauth_app_id, _ = _extract_oauth_app_id_from_state(state or "")

        await oauth.exchange_code(
            p,
            code,
            oauth_app_id=oauth_app_id,
            state=state or "",
        )
        return RedirectResponse(
            url=f"{frontend_url.rstrip('/')}/creators?social=connected&platform={platform}"
        )
    except (ValueError, InvalidGrantError) as e:
        log.warning("OAuth exchange failed for %s: %s", platform, e)
        if isinstance(e, InvalidGrantError):
            msg = (
                "Ошибка YouTube OAuth: код истёк, уже использован или redirect_uri не совпадает. "
                "Проверьте docs/SOCIAL_PLATFORMS.md"
            )
        else:
            msg = str(e)[:100]
        return RedirectResponse(
            url=f"{frontend_url.rstrip('/')}/creators?social=error&message={quote(msg, safe='')}"
        )


@router.patch("/accounts/{account_id}", response_model=SocialAccountResponse)
async def update_account(
    account_id: str,
    data: SocialAccountUpdate,
    oauth: OAuthService = Depends(get_oauth_service),
    repo: SocialAccountRepository = Depends(get_social_account_repository),
) -> SocialAccountResponse:
    """Update social account (e.g. display name). Only own accounts."""
    try:
        uid = oauth.get_user_id()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    acc = await repo.get_by_id(UUID(account_id))
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    if acc.user_id != uid:
        raise HTTPException(status_code=403, detail="Нет доступа")

    updated = await repo.update_channel_title(UUID(account_id), data.channel_title)
    if not updated:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")

    return SocialAccountResponse(
        id=updated.id,
        platform=updated.platform.value,
        channel_id=updated.channel_id,
        channel_title=updated.channel_title,
        created_at=updated.created_at.isoformat() if updated.created_at else "",
    )


@router.delete("/accounts/{account_id}", status_code=204)
async def disconnect_account(
    account_id: str,
    oauth: OAuthService = Depends(get_oauth_service),
    repo: SocialAccountRepository = Depends(get_social_account_repository),
) -> None:
    """Disconnect (delete) social account. Only own accounts."""
    try:
        uid = oauth.get_user_id()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    acc = await repo.get_by_id(UUID(account_id))
    if not acc:
        raise HTTPException(status_code=404, detail="Аккаунт не найден")
    if acc.user_id != uid:
        raise HTTPException(status_code=403, detail="Нет доступа")

    await repo.delete(acc.id)


@router.get("/accounts", response_model=SocialAccountsListResponse)
async def list_accounts(
    oauth: OAuthService = Depends(get_oauth_service),
    repo: SocialAccountRepository = Depends(get_social_account_repository),
) -> SocialAccountsListResponse:
    """List connected social accounts for current user (MVP: DEFAULT_USER_ID)."""
    try:
        user_id = oauth.get_user_id()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    accounts = await repo.list_by_user(user_id)
    return SocialAccountsListResponse(
        accounts=[
            SocialAccountResponse(
                id=a.id,
                platform=a.platform.value,
                channel_id=a.channel_id,
                channel_title=a.channel_title,
                created_at=a.created_at.isoformat() if a.created_at else "",
            )
            for a in accounts
        ]
    )


# OAuth App Credentials endpoints


@router.get("/oauth-apps", response_model=OAuthAppListResponse)
async def list_oauth_apps(
    platform: str | None = Query(None, description="Filter by platform"),
    oauth: OAuthService = Depends(get_oauth_service),
    service: OAuthAppCredentialsService = Depends(get_oauth_app_credentials_service),
) -> OAuthAppListResponse:
    """List OAuth app credentials for current user."""
    try:
        user_id = oauth.get_user_id()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        apps = await service.list_credentials(platform=platform, user_id=user_id)
        return OAuthAppListResponse(apps=apps)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.post("/oauth-apps", response_model=OAuthAppRead, status_code=201)
async def create_oauth_app(
    data: OAuthAppCreate,
    oauth: OAuthService = Depends(get_oauth_service),
    service: OAuthAppCredentialsService = Depends(get_oauth_app_credentials_service),
) -> OAuthAppRead:
    """Create OAuth app credentials."""
    try:
        user_id = oauth.get_user_id()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        app = await service.create_credentials(data, user_id=user_id)
        return app
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.patch("/oauth-apps/{app_id}", response_model=OAuthAppRead)
async def update_oauth_app(
    app_id: UUID,
    data: OAuthAppUpdate,
    oauth: OAuthService = Depends(get_oauth_service),
    service: OAuthAppCredentialsService = Depends(get_oauth_app_credentials_service),
) -> OAuthAppRead:
    """Update OAuth app credentials (partial)."""
    try:
        user_id = oauth.get_user_id()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    try:
        app = await service.update_credentials(app_id, data, user_id=user_id)
        if not app:
            raise HTTPException(status_code=404, detail="OAuth приложение не найдено")
        return app
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


@router.delete("/oauth-apps/{app_id}", status_code=204)
async def delete_oauth_app(
    app_id: UUID,
    oauth: OAuthService = Depends(get_oauth_service),
    service: OAuthAppCredentialsService = Depends(get_oauth_app_credentials_service),
) -> None:
    """Delete OAuth app credentials."""
    try:
        user_id = oauth.get_user_id()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e

    deleted = await service.delete_credentials(app_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="OAuth приложение не найдено")
