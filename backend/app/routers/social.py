"""Social OAuth router. No business logic in router."""

from __future__ import annotations

import logging
from uuid import UUID
from urllib.parse import quote

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
)
from app.services.social.oauth_app_credentials_service import OAuthAppCredentialsService
from app.services.social.oauth_service import OAuthService

log = logging.getLogger(__name__)

router = APIRouter(prefix="/social", tags=["social"])


def _parse_platform(platform: str) -> SocialPlatform:
    """Parse platform string to enum. Raises 400 if invalid."""
    try:
        return SocialPlatform(platform.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Платформа не поддерживается")


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
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str = Query(..., description="Authorization code from OAuth provider"),
    state: str = Query(..., description="OAuth state parameter (contains oauth_app_id)"),
    device_id: str | None = Query(None, description="VK ID device_id"),
    oauth: OAuthService = Depends(get_oauth_service),
) -> RedirectResponse:
    """OAuth callback. Exchange code for tokens, redirect to frontend. 
    oauth_app_id is extracted from state parameter."""
    p = _parse_platform(platform)
    frontend_url = get_settings().FRONTEND_URL
    try:
        # Extract oauth_app_id from state parameter
        from app.services.social.oauth_service import _extract_oauth_app_id_from_state
        oauth_app_id, original_state = _extract_oauth_app_id_from_state(state)
        
        await oauth.exchange_code(p, code, oauth_app_id=oauth_app_id, state=original_state, device_id=device_id)
        return RedirectResponse(url=f"{frontend_url}/?social=connected&platform={platform}")
    except (ValueError, InvalidGrantError) as e:
        log.warning("OAuth exchange failed for %s: %s", platform, e)
        if isinstance(e, InvalidGrantError):
            msg = (
                "Ошибка YouTube OAuth: код истёк, уже использован или redirect_uri не совпадает. "
                "Проверьте docs/SOCIAL_PLATFORMS.md"
            )
        else:
            msg = str(e)[:100]
        return RedirectResponse(url=f"{frontend_url}/?social=error&message={quote(msg, safe='')}")


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
        raise HTTPException(status_code=400, detail=str(e))

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
        raise HTTPException(status_code=400, detail=str(e))

    try:
        apps = await service.list_credentials(platform=platform, user_id=user_id)
        return OAuthAppListResponse(apps=apps)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        raise HTTPException(status_code=400, detail=str(e))

    try:
        app = await service.create_credentials(data, user_id=user_id)
        return app
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        raise HTTPException(status_code=400, detail=str(e))

    try:
        app = await service.update_credentials(app_id, data, user_id=user_id)
        if not app:
            raise HTTPException(status_code=404, detail="OAuth приложение не найдено")
        return app
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


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
        raise HTTPException(status_code=400, detail=str(e))

    deleted = await service.delete_credentials(app_id, user_id=user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="OAuth приложение не найдено")
