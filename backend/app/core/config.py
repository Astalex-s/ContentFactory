"""Application configuration via environment variables."""

from functools import lru_cache
from typing import List

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
    CORS_ORIGINS: str = "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000,http://127.0.0.1:3000"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Database (required, set via .env — no default to avoid hardcoded credentials)
    DATABASE_URL: str = ""  # Must be set in .env

    # AI (OpenAI)
    AI_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-5-mini-2025-08-07"
    AI_TIMEOUT: int = 60

    # Replicate (image generation)
    REPLICATE_API_TOKEN: str = ""
    IMAGE_PROVIDER: str = "replicate"
    REPLICATE_DELAY_SECONDS: int = 15  # Задержка между запросами (rate limit)
    REPLICATE_IMAGE_MODEL: str = "stability-ai/stable-diffusion-img2img:15a3689ee13b0d2616e98820eca31d4c3abcd36672df6afce5cb6feb1d66087d"
    REPLICATE_VIDEO_MODEL: str = "kwaivgi/kling-v2.1:daad218feb714b03e2a1ac445986aebb9d05243cd00da2af17be2e4049f48f69"
    REPLICATE_VIDEO_DURATION: int = 10  # секунд (5–20 для Kling; SVD ограничен ~4 сек)

    # Media storage
    MEDIA_BASE_PATH: str = "/app/media"

    # Rate limit for content generation
    CONTENT_GENERATE_RATE_LIMIT: str = "10/minute"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance."""
    return Settings()


def get_cors_origins() -> List[str]:
    """Parse CORS_ORIGINS into list."""
    settings = get_settings()
    return [origin.strip() for origin in settings.CORS_ORIGINS.split(",") if origin.strip()]
