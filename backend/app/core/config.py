"""Application configuration via environment variables."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    APP_NAME: str = "ContentFactory"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # CORS (comma-separated origins)
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Database (required — no default to avoid hardcoded credentials)
    DATABASE_URL: str = ""

    # AI (OpenAI)
    AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    AI_TIMEOUT: int = 60

    # Replicate (image/video generation)
    REPLICATE_API_TOKEN: str = ""
    IMAGE_PROVIDER: str = "replicate"
    REPLICATE_DELAY_SECONDS: int = 15
    REPLICATE_IMAGE_MODEL: str = "black-forest-labs/flux-kontext-pro"
    REPLICATE_VIDEO_MODEL: str = "wan-video/wan-2.2-i2v-fast"
    REPLICATE_VIDEO_DURATION: int = 6

    # Media storage: local | s3
    STORAGE_BACKEND: str = "local"
    MEDIA_BASE_PATH: str = "/app/media"

    # S3 (only when STORAGE_BACKEND=s3)
    S3_ACCESS_KEY_ID: str = ""
    S3_SECRET_ACCESS_KEY: str = ""
    S3_BUCKET: str = ""
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: str = ""
    S3_PUBLIC_URL: str = ""
    S3_PRESIGNED_EXPIRE: int = 3600

    # Rate limit for content generation
    CONTENT_GENERATE_RATE_LIMIT: str = "10/minute"

    # OAuth & Social (credentials stored encrypted in DB)
    OAUTH_SECRET_KEY: str = ""
    OAUTH_ENCRYPTION_SALT: str = ""
    DEFAULT_USER_ID: str = "00000000-0000-0000-0000-000000000001"
    API_BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    SOCIAL_TIMEOUT: int = 60

    # VK video upload (community token)
    VK_SERVICE_KEY: str = ""
    VK_GROUP_ID: str = ""
    VK_COMMUNITY_TOKEN: str = ""


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


def get_cors_origins() -> list[str]:
    """Parse CORS_ORIGINS into list."""
    settings = get_settings()
    return [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
