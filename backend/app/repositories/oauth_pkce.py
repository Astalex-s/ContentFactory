"""Repository for OAuth PKCE state (code_verifier storage)."""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.oauth_pkce import OAuthPkceState


class OAuthPkceRepository:
    """Repository for PKCE state CRUD."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def store(self, state: str, code_verifier: str, expires_at: datetime) -> None:
        """Store code_verifier by state."""
        row = OAuthPkceState(
            state=state,
            code_verifier=code_verifier,
            expires_at=expires_at,
        )
        self.session.add(row)
        await self.session.flush()

    async def pop(self, state: str) -> str | None:
        """Get and delete code_verifier by state. Returns None if expired or not found."""
        stmt = select(OAuthPkceState).where(OAuthPkceState.state == state)
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return None
        now = datetime.now(UTC)
        if row.expires_at and row.expires_at < now:
            await self.session.delete(row)
            await self.session.flush()
            return None
        code_verifier = row.code_verifier
        await self.session.delete(row)
        await self.session.flush()
        return code_verifier

    async def pop_by_state_prefix(self, prefix: str) -> tuple[str, str] | None:
        """Find and pop state that starts with 'prefix:'. Returns (full_state, code_verifier) or None."""
        escaped = prefix.replace("%", "\\%").replace("_", "\\_")
        stmt = (
            select(OAuthPkceState)
            .where(OAuthPkceState.state.like(f"{escaped}:%"))
            .order_by(OAuthPkceState.expires_at.desc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        row = result.scalar_one_or_none()
        if not row:
            return None
        now = datetime.now(UTC)
        if row.expires_at and row.expires_at < now:
            await self.session.delete(row)
            await self.session.flush()
            return None
        full_state = row.state
        code_verifier = row.code_verifier
        await self.session.delete(row)
        await self.session.flush()
        return (full_state, code_verifier)
