"""Content generation router."""

from __future__ import annotations

import logging
import uuid
from uuid import UUID

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, Request
from fastapi.responses import FileResponse, Response

from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.dependencies import (
    get_content_service,
    get_image_generation_service,
    get_media_storage,
    get_text_generation_service,
)
from app.schemas.generated_content import (
    ContentListResponse,
    CreatePostTextRequest,
    GenerateContentRequest,
    GenerateContentResponse,
    GeneratePostTextRequest,
    GeneratePostTextResponse,
    TaskResponse,
    UpdateContentRequest,
)
from app.services.content_service import ContentService
from app.services.image.image_generation_service import ImageGenerationService
from app.services.media import LocalFileStorage, get_storage
from app.services.task_status_service import get_task_status_service
from app.services.text_generation_service import TextGenerationService
from app.services.video.video_generation_service import VideoGenerationService

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


@router.post(
    "/product/{product_id}/generate-post-text",
    response_model=GeneratePostTextResponse,
)
@limiter.limit(get_settings().CONTENT_GENERATE_RATE_LIMIT)
async def generate_post_text(
    request: Request,
    product_id: UUID,
    body: GeneratePostTextRequest | None = None,
    service: TextGenerationService = Depends(get_text_generation_service),
) -> GeneratePostTextResponse:
    """Generate title and text for VK post (optionally with video link)."""
    video_url = (body and body.video_url) or None
    result = await service.generate_post_text(product_id, video_url=video_url)
    if result is None:
        raise HTTPException(status_code=404, detail="Товар не найден")
    title, text = result
    return GeneratePostTextResponse(title=title, text=text)


@router.post("/product/{product_id}/post-text")
@limiter.limit(get_settings().CONTENT_GENERATE_RATE_LIMIT)
async def create_post_text(
    request: Request,
    product_id: UUID,
    body: CreatePostTextRequest,
    content_svc: ContentService = Depends(get_content_service),
) -> dict:
    """Create text content for VK post. Returns content id for publishing."""
    content = await content_svc.create_post_text(
        product_id=product_id,
        title=body.title,
        text=body.text,
        video_url=body.video_url,
    )
    return {"id": str(content.id), "content_text": content.content_text}


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


@router.patch("/{content_id}/approve")
async def approve_content(
    content_id: UUID,
    approved: bool = Query(..., description="Одобрен для авто-публикации"),
    service: ContentService = Depends(get_content_service),
):
    """Установить одобрение контента для авто-публикации."""
    result = await service.set_approved_for_publication(content_id, approved)
    if result is None:
        raise HTTPException(status_code=404, detail="Контент не найден")
    return result


@router.delete("/{content_id}", status_code=204)
async def delete_content(
    content_id: UUID,
    service: ContentService = Depends(get_content_service),
    media=Depends(get_media_storage),
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

    task_svc = get_task_status_service()
    await task_svc.set_status(task_id, "running", progress=10, message="Генерация изображений")
    try:
        async with async_session_maker() as session:
            product_repo = ProductRepository(session)
            content_repo = GeneratedContentRepository(session)
            media = get_storage()
            svc = ImageGenerationService(product_repo, content_repo, media)
            await svc.generate_images_for_product(product_id, count=1)
            await session.commit()
        await task_svc.set_status(task_id, "completed", progress=100, message="Изображения созданы")
    except Exception as e:
        log.exception("Image generation failed for product %s: %s", product_id, e)
        await task_svc.set_status(task_id, "failed", progress=0, error=str(e))


async def _run_video_generation(
    task_id: str,
    product_id: UUID,
    image_content_id: UUID | None,
) -> None:
    """Background: generate video for product (async, same event loop)."""
    from app.core.database import async_session_maker
    from app.repositories.generated_content import GeneratedContentRepository
    from app.repositories.product import ProductRepository

    task_svc = get_task_status_service()
    await task_svc.set_status(task_id, "running", progress=10, message="Генерация видео")
    try:
        async with async_session_maker() as session:
            product_repo = ProductRepository(session)
            content_repo = GeneratedContentRepository(session)
            media = get_storage()
            svc = VideoGenerationService(product_repo, content_repo, media)
            await svc.generate_video_for_product(product_id, image_content_id=image_content_id)
            await session.commit()
        await task_svc.set_status(task_id, "completed", progress=100, message="Видео создано")
    except Exception as e:
        log.exception("Video generation failed for product %s: %s", product_id, e)
        await task_svc.set_status(task_id, "failed", progress=0, error=str(e))


@router.post("/images/{product_id}", response_model=TaskResponse)
@limiter.limit(get_settings().CONTENT_GENERATE_RATE_LIMIT)
async def generate_images(
    request: Request,
    product_id: UUID,
    background_tasks: BackgroundTasks,
    image_svc: ImageGenerationService = Depends(get_image_generation_service),
) -> TaskResponse:
    """Start generation of 1 image. Returns task_id."""
    task_id = str(uuid.uuid4())
    task_svc = get_task_status_service()
    await task_svc.set_status(task_id, "pending", progress=0, message="Ожидание генерации")
    background_tasks.add_task(_run_image_generation, task_id, product_id)
    return TaskResponse(task_id=task_id, status="pending")


@router.post("/video/{product_id}", response_model=TaskResponse)
@limiter.limit(get_settings().CONTENT_GENERATE_RATE_LIMIT)
async def generate_video(
    request: Request,
    product_id: UUID,
    background_tasks: BackgroundTasks,
    image_content_id: UUID | None = Query(
        None, description="Use this image; default: main product image"
    ),
) -> TaskResponse:
    """Start video generation. Returns task_id."""
    task_id = str(uuid.uuid4())
    task_svc = get_task_status_service()
    await task_svc.set_status(task_id, "pending", progress=0, message="Ожидание генерации")
    background_tasks.add_task(_run_video_generation, task_id, product_id, image_content_id)
    return TaskResponse(task_id=task_id, status="pending")


@router.get("/media/{file_path:path}", response_model=None)
async def get_media_file(
    file_path: str,
    media=Depends(get_media_storage),
):
    """Serve media. Local: FileResponse. S3: redirect to presigned URL."""
    # Нормализуем путь (защита от path traversal в LocalFileStorage)
    key = file_path.replace("\\", "/").lstrip("/")
    if not key:
        raise HTTPException(status_code=400, detail="Invalid path")

    try:
        url = await media.get_url(key)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid path") from e

    # S3: presigned URL — редирект
    if url.startswith("http://") or url.startswith("https://"):
        from fastapi.responses import RedirectResponse

        return RedirectResponse(url=url, status_code=302)

    # Local: отдаём файл
    if isinstance(media, LocalFileStorage):
        try:
            full_path = media.get_full_path(key)
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid path") from e
        if not full_path.exists() or not full_path.is_file():
            raise HTTPException(status_code=404, detail="Файл не найден")
        media_type = "video/mp4" if key.startswith("videos/") else "image/png"
        return FileResponse(
            path=str(full_path),
            media_type=media_type,
            filename=full_path.name,
            content_disposition_type="inline",
        )

    # Local fallback: download и Response (если не LocalFileStorage с get_full_path)
    try:
        data = await media.download(key)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail="Файл не найден") from e
    media_type = "video/mp4" if key.startswith("videos/") else "image/png"
    return Response(content=data, media_type=media_type)
