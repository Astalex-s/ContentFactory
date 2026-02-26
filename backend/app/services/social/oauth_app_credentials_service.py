"""Service for managing OAuth app credentials."""

import logging
import uuid
from typing import Optional

from app.core.config import get_settings
from app.core.encryption import decrypt_token, encrypt_token
from app.models.oauth_app_credentials import OAuthAppCredentials
from app.models.social_account import SocialPlatform
from app.repositories.oauth_app_credentials import OAuthAppCredentialsRepository
from app.schemas.social import OAuthAppCreate, OAuthAppRead, OAuthAppUpdate

log = logging.getLogger(__name__)
settings = get_settings()


class OAuthAppCredentialsService:
    """Service for OAuth app credentials CRUD with encryption."""

    def __init__(self, repository: OAuthAppCredentialsRepository) -> None:
        self.repository = repository

    async def create_credentials(
        self, data: OAuthAppCreate, user_id: Optional[uuid.UUID] = None
    ) -> OAuthAppRead:
        """Create OAuth app credentials. Encrypts client_secret."""
        try:
            platform = SocialPlatform(data.platform)
        except ValueError as e:
            raise ValueError(f"Invalid platform: {data.platform}") from e

        if not data.name.strip():
            raise ValueError("Name cannot be empty")
        if not data.client_id.strip():
            raise ValueError("Client ID cannot be empty")
        if not data.client_secret.strip():
            raise ValueError("Client secret cannot be empty")

        encrypted_secret = encrypt_token(
            data.client_secret, settings.OAUTH_SECRET_KEY, settings.OAUTH_ENCRYPTION_SALT
        )

        app = await self.repository.create(
            user_id=user_id,
            platform=platform,
            name=data.name,
            client_id=data.client_id,
            client_secret_encrypted=encrypted_secret,
            redirect_uri=data.redirect_uri,
        )

        return self._to_read_schema(app)

    async def update_credentials(
        self, app_id: uuid.UUID, data: OAuthAppUpdate, user_id: Optional[uuid.UUID] = None
    ) -> Optional[OAuthAppRead]:
        """Update OAuth app credentials (partial). Encrypts client_secret if provided."""
        app = await self.repository.get_by_id(app_id)
        if not app:
            return None

        if user_id is not None and app.user_id != user_id:
            log.warning("User %s attempted to update app %s owned by %s", user_id, app_id, app.user_id)
            return None

        encrypted_secret = None
        if data.client_secret is not None:
            if not data.client_secret.strip():
                raise ValueError("Client secret cannot be empty")
            encrypted_secret = encrypt_token(
                data.client_secret, settings.OAUTH_SECRET_KEY, settings.OAUTH_ENCRYPTION_SALT
            )

        updated = await self.repository.update(
            app_id=app_id,
            name=data.name,
            client_id=data.client_id,
            client_secret_encrypted=encrypted_secret,
            redirect_uri=data.redirect_uri,
        )
        if not updated:
            return None
        return self._to_read_schema(updated)

    async def list_credentials(
        self, platform: Optional[str] = None, user_id: Optional[uuid.UUID] = None
    ) -> list[OAuthAppRead]:
        """List OAuth app credentials, optionally filtered by platform."""
        platform_enum = None
        if platform:
            try:
                platform_enum = SocialPlatform(platform)
            except ValueError as e:
                raise ValueError(f"Invalid platform: {platform}") from e

        apps = await self.repository.list_by_platform(platform=platform_enum, user_id=user_id)
        return [self._to_read_schema(app) for app in apps]

    async def delete_credentials(
        self, app_id: uuid.UUID, user_id: Optional[uuid.UUID] = None
    ) -> bool:
        """Delete OAuth app credentials. Returns True if deleted."""
        app = await self.repository.get_by_id(app_id)
        if not app:
            return False

        if user_id is not None and app.user_id != user_id:
            log.warning("User %s attempted to delete app %s owned by %s", user_id, app_id, app.user_id)
            return False

        return await self.repository.delete(app_id)

    async def get_credentials_decrypted(
        self, app_id: uuid.UUID
    ) -> Optional[tuple[str, str, Optional[str]]]:
        """Get decrypted credentials (client_id, client_secret, redirect_uri). For internal use only."""
        app = await self.repository.get_by_id(app_id)
        if not app:
            return None

        decrypted_secret = decrypt_token(
            app.client_secret, settings.OAUTH_SECRET_KEY, settings.OAUTH_ENCRYPTION_SALT
        )
        if not decrypted_secret:
            log.error("Failed to decrypt client_secret for app %s", app_id)
            return None

        return (app.client_id, decrypted_secret, app.redirect_uri)

    def _to_read_schema(self, app: OAuthAppCredentials) -> OAuthAppRead:
        """Convert model to read schema with masked client_id."""
        client_id_masked = self._mask_client_id(app.client_id)
        return OAuthAppRead(
            id=app.id,
            user_id=app.user_id,
            platform=app.platform.value,
            name=app.name,
            client_id_masked=client_id_masked,
            redirect_uri=app.redirect_uri,
            created_at=app.created_at,
            updated_at=app.updated_at,
        )

    @staticmethod
    def _mask_client_id(client_id: str) -> str:
        """Mask client_id, show only last 4 chars."""
        if len(client_id) <= 4:
            return "••••"
        return "••••" + client_id[-4:]
