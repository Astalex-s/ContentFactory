"""Content generation router."""

from __future__ import annotations

import logging
import uuid
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.dependencies import (
    get_content_service,
    get_image_generation_service,
    get_media_storage,
    get_text_generation_service,
    get_video_generation_service,
)
from app.schemas.generated_content import (
    ContentListResponse,
    GenerateContentRequest,
    GenerateContentResponse,
    TaskResponse,
    UpdateContentRequest,
)
from app.services.content_service import ContentService
from app.services.image.image_generation_service import ImageGenerationService
from app.services.media import MediaStorageService
from app.services.text_generation_service import TextGenerationService
from app.services.video.video_generation_service import VideoGenerationService
from app.services.task_status_service import get_task_status_service

log = logging.getLogger(__name__)

router = APIRouter(prefix="/content", tags=["content"])


@router.post(
    "/generate/{product_id}",
    response_model=GenerateContentResponse,
)
@limiter.limit(get_settings().CONTENT_GENERATE_RATE_LIMIT)
async def generate_content(
    request: Request,
    product_id: UUID,
    body: GenerateContentRequest,
    service: TextGenerationService = Depends(get_text_generation_service),
) -> GenerateContentResponse:
    """
    Generate text content variants for product.

    Returns 404 if product not found.
    """
    try:
        result = await service.generate_for_product(
            product_id=product_id,
            platform=body.platform,
            tone=body.tone,
            content_text_type=body.content_text_type,
        )
    except Exception as e:
        log.error("Content generation failed: %s", str(e))
        raise HTTPException(
            status_code=500,
            detail="Ошибка генерации контента. Попробуйте позже.",
        ) from e

    if result is None:
        raise HTTPException(status_code=404, detail="Товар не найден")

    return result


@router.post("/product/{product_id}/generate-video-title")
@limiter.limit(get_settings().CONTENT_GENERATE_RATE_LIMIT)
async def generate_video_title(
    request: Request,
    product_id: UUID,
    service: TextGenerationService = Depends(get_text_generation_service),
) -> dict:
    """Generate short Russian video title for product. Returns product name if not found."""
    title = await service.generate_video_title(product_id)
    if title is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    return {"title": title}


@router.get("/product/{product_id}/has")
async def has_content(
    product_id: UUID,
    service: ContentService = Depends(get_content_service),
) -> dict:
    """Check if product has any generated content."""
    return {"has_content": await service.has_content(product_id)}


@router.get(
    "/all",
    response_model=ContentListResponse,
)
async def list_all_content(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ContentService = Depends(get_content_service),
) -> ContentListResponse:
    """Get paginated list of all generated content."""
    return await service.get_all(
        page=page,
        page_size=page_size,
    )


@router.get(
    "/product/{product_id}",
    response_model=ContentListResponse,
)
async def list_content_by_product(
    product_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    service: ContentService = Depends(get_content_service),
) -> ContentListResponse:
    """Get paginated list of generated content for product."""
    return await service.get_by_product(
        product_id=product_id,
        page=page,
        page_size=page_size,
    )


@router.patch("/{content_id}")
async def update_content(
    content_id: UUID,
    body: UpdateContentRequest,
    service: ContentService = Depends(get_content_service),
):
    """Update content text (draft only)."""
    result = await service.update_text(content_id, body.content_text)
    if result is None:
        raise HTTPException(
            status_code=400,
            detail="Контент не найден или редактирование недоступно (только draft).",
        )
    return result


@router.delete("/{content_id}", status_code=204)
async def delete_content(
    content_id: UUID,
    service: ContentService = Depends(get_content_service),
    media: MediaStorageService = Depends(get_media_storage),
) -> None:
    """Delete content."""
    deleted = await service.delete(content_id, media)
    if not deleted:
        raise HTTPException(status_code=404, detail="Контент не найден")


# --- Stage 3: Images and Video ---


async def _run_image_generation(
    task_id: str,
    product_id: UUID,
) -> None:
    """Background: generate images for product (async, same event loop)."""
    from app.core.database import async_session_maker
    from app.repositories.generated_content import GeneratedContentRepository
    from app.repositories.product import ProductRepository
    from app.services.media import MediaStorageService

    task_svc = get_task_status_service()
    task_svc.set_status(task_id, "running", progress=10, message="Генерация изображений")
    try:
        async with async_session_maker() as session:
            product_repo = ProductRepository(session)
            content_repo = GeneratedContentRepository(session)
            media = MediaStorageService()
            svc = ImageGenerationService(product_repo, content_repo, media)
            result = await svc.generate_images_for_product(product_id, count=3)
            await session.commit()
        task_svc.set_status(task_id, "completed", progress=100, message="Изображения созданы")
    except Exception as e:
        log.exception("Image generation failed for product %s: %s", product_id, e)
        task_svc.set_status(task_id, "failed", progress=0, error=str(e))


async def _run_video_generation(
    task_id: str,
    product_id: UUID,
    image_content_id: UUID | None,
) -> None:
    """Background: generate video for product (async, same event loop)."""
    from app.core.database import async_session_maker
    from app.repositories.generated_content import GeneratedContentRepository
    from app.repositories.product import ProductRepository
    from app.services.media import MediaStorageService

    task_svc = get_task_status_service()
    task_svc.set_status(task_id, "running", progress=10, message="Генерация видео")
    try:
        async with async_session_maker() as session:
            product_repo = ProductRepository(session)
            content_repo = GeneratedContentRepository(session)
            media = MediaStorageService()
            svc = VideoGenerationService(product_repo, content_repo, media)
            result = await svc.generate_video_for_product(
                product_id, image_content_id=image_content_id
            )
            await session.commit()
        task_svc.set_status(task_id, "completed", progress=100, message="Видео создано")
    except Exception as e:
        log.exception("Video generation failed for product %s: %s", product_id, e)
        task_svc.set_status(task_id, "failed", progress=0, error=str(e))


@router.post("/images/{product_id}", response_model=TaskResponse)
@limiter.limit(get_settings().CONTENT_GENERATE_RATE_LIMIT)
async def generate_images(
    request: Request,
    product_id: UUID,
    background_tasks: BackgroundTasks,
    image_svc: ImageGenerationService = Depends(get_image_generation_service),
) -> TaskResponse:
    """Start generation of 3 images. Returns task_id."""
    task_id = str(uuid.uuid4())
    task_svc = get_task_status_service()
    task_svc.set_status(task_id, "pending", progress=0, message="Ожидание генерации")
    background_tasks.add_task(_run_image_generation, task_id, product_id)
    return TaskResponse(task_id=task_id, status="pending")


@router.post("/video/{product_id}", response_model=TaskResponse)
@limiter.limit(get_settings().CONTENT_GENERATE_RATE_LIMIT)
async def generate_video(
    request: Request,
    product_id: UUID,
    background_tasks: BackgroundTasks,
    image_content_id: UUID | None = Query(None, description="Use this image; default: main product image"),
) -> TaskResponse:
    """Start video generation. Returns task_id."""
    task_id = str(uuid.uuid4())
    task_svc = get_task_status_service()
    task_svc.set_status(task_id, "pending", progress=0, message="Ожидание генерации")
    background_tasks.add_task(_run_video_generation, task_id, product_id, image_content_id)
    return TaskResponse(task_id=task_id, status="pending")


@router.get("/media/{file_path:path}", response_model=None)
async def get_media_file(
    file_path: str,
    media: MediaStorageService = Depends(get_media_storage),
):
    """Serve media. FileResponse handles Range (206) automatically. Use inline for video playback."""
    from pathlib import Path
    
    # Защита от path traversal
    full_path = media.get_full_path(file_path)
    base_path = Path(get_settings().MEDIA_BASE_PATH).resolve()
    
    try:
        resolved_path = full_path.resolve()
    except (ValueError, OSError):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    # Проверяем, что путь находится внутри MEDIA_BASE_PATH
    if not str(resolved_path).startswith(str(base_path)):
        raise HTTPException(status_code=400, detail="Invalid path")
    
    if not resolved_path.exists() or not resolved_path.is_file():
        raise HTTPException(status_code=404, detail="Файл не найден")
    
    media_type = "video/mp4" if file_path.startswith("videos/") else "image/png"
    return FileResponse(
        path=str(resolved_path),
        media_type=media_type,
        filename=resolved_path.name,
        content_disposition_type="inline",
    )


