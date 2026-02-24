"""Social OAuth router. No business logic in router."""

from __future__ import annotations

import logging
from uuid import UUID
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from oauthlib.oauth2.rfc6749.errors import InvalidGrantError

from app.core.config import get_settings
from app.dependencies import get_oauth_service, get_social_repo
from app.models.social_account import SocialPlatform
from app.repositories.social_account import SocialAccountRepository
from app.schemas.social import SocialAccountResponse, SocialAccountsListResponse
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
    oauth: OAuthService = Depends(get_oauth_service),
) -> dict:
    """Get OAuth authorization URL. Redirect user to this URL."""
    p = _parse_platform(platform)
    try:
        auth_url = oauth.get_auth_url(p)
        return {"auth_url": auth_url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/callback/{platform}")
async def oauth_callback(
    platform: str,
    code: str = Query(..., description="Authorization code from OAuth provider"),
    oauth: OAuthService = Depends(get_oauth_service),
) -> RedirectResponse:
    """OAuth callback. Exchange code for tokens, redirect to frontend."""
    p = _parse_platform(platform)
    frontend_url = get_settings().FRONTEND_URL
    try:
        await oauth.exchange_code(p, code)
        return RedirectResponse(url=f"{frontend_url}/?social=connected&platform={platform}")
    except (ValueError, InvalidGrantError) as e:
        log.warning("OAuth exchange failed: %s", e)
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
    repo: SocialAccountRepository = Depends(get_social_repo),
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
    repo: SocialAccountRepository = Depends(get_social_repo),
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
