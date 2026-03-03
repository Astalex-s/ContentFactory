"""FastAPI application entry point."""

# S3-compatible storage (Beget, B2, etc.) may not support checksum headers.
# Set before any boto3/aiobotocore imports.
import os

os.environ.setdefault("AWS_REQUEST_CHECKSUM_CALCULATION", "when_required")
os.environ.setdefault("AWS_RESPONSE_CHECKSUM_VALIDATION", "when_required")

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.ai_middleware import AITimingMiddleware
from app.core.config import get_cors_origins, get_settings
from app.core.logging import setup_logging
from app.core.rate_limit import limiter
from app.routers import (
    analytics,
    content,
    dashboard,
    health,
    products,
    publish,
    social,
    tasks,
)
from app.routers import (
    settings as settings_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup and shutdown."""
    import asyncio
    import logging

    from app.services.status_sync_service import run_status_sync_task

    setup_logging()
    log = logging.getLogger("app.main")
    log.info("Application startup")

    # Load publish rate limit setting from DB
    try:
        from app.core.database import async_session_maker
        from app.core.publish_rate_limit import set_publish_rate_limit_enabled
        from app.repositories.app_settings import AppSettingsRepository

        async with async_session_maker() as session:
            repo = AppSettingsRepository(session)
            val = await repo.get("publish_rate_limit_enabled")
            set_publish_rate_limit_enabled(val != "false")
    except Exception as e:
        log.warning("Could not load publish_rate_limit_enabled: %s", e)

    async def _status_sync_loop() -> None:
        """Periodic status sync. MVP: every 60s. Replace with Celery when scaling."""
        while True:
            try:
                await asyncio.sleep(60)
                await run_status_sync_task()
            except asyncio.CancelledError:
                break
            except Exception as e:
                log.warning("Status sync error: %s", e)

    sync_task = asyncio.create_task(_status_sync_loop())

    yield

    sync_task.cancel()
    try:
        await sync_task
    except asyncio.CancelledError:
        pass
    log.info("Application shutdown")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_cors_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["Accept-Ranges", "Content-Range", "Content-Length"],
    )
    app.add_middleware(AITimingMiddleware)

    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    async def _validation_exception_handler(
        _request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        """Понятные сообщения об ошибках валидации (UUID, Field required)."""
        errs = exc.errors()
        seen: set[str] = set()
        msgs: list[str] = []
        for e in errs:
            loc_parts = [str(x) for x in e.get("loc", []) if x != "body"]
            loc = ".".join(loc_parts)
            msg = e.get("msg", "")
            if "content_id" in loc:
                if "content_id" not in seen:
                    seen.add("content_id")
                    msgs.append(
                        "content_id: неверный формат (выберите видео или обновите страницу)"
                    )
            elif "account_id" in loc:
                if "account_id" not in seen:
                    seen.add("account_id")
                    msgs.append("account_id: выберите аккаунт YouTube")
            elif "platform" in loc:
                if "platform" not in seen:
                    seen.add("platform")
                    msgs.append("platform: выберите платформу (youtube)")
            elif "UUID" in msg or "uuid" in msg.lower():
                if loc not in seen:
                    seen.add(loc)
                    msgs.append(
                        f"{loc or 'поле'}: неверный формат UUID (возможно передано 'undefined' или 'null')"
                    )
            elif "Field required" in msg:
                if loc not in seen:
                    seen.add(loc)
                    msgs.append(f"{loc or 'поле'}: обязательно для заполнения")
            else:
                msgs.append(f"{loc or 'поле'}: {msg}")
        return JSONResponse(
            status_code=422,
            content={"detail": "; ".join(msgs) if msgs else str(exc)},
        )

    app.add_exception_handler(
        RequestValidationError,
        _validation_exception_handler,  # type: ignore[arg-type]
    )

    app.include_router(health.router)
    app.include_router(products.router)
    app.include_router(content.router)
    app.include_router(tasks.router)
    app.include_router(social.router)
    app.include_router(publish.router)
    app.include_router(analytics.router)
    app.include_router(dashboard.router)
    app.include_router(settings_router.router)

    media_dir = Path(settings.MEDIA_BASE_PATH)
    if media_dir.exists():
        app.mount("/media", StaticFiles(directory=str(media_dir)), name="media")

    return app


app = create_app()
