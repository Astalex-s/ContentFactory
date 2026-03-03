"""Marketplace import service: GPT + Replicate for product generation."""

from __future__ import annotations

import asyncio
import json
import logging
import uuid
from typing import Any

from app.core.config import get_settings
from app.models.product import Product
from app.repositories.product import ProductRepository
from app.services.ai.ai_factory import get_ai_provider
from app.services.image.replicate_provider import generate_image_replicate

log = logging.getLogger(__name__)

PRODUCTS_COUNT = 5

PROMPT_PRODUCTS = """Сгенерируй ровно 5 товаров для дома в формате JSON-массива.

Товары ТОЛЬКО для дома и быта: полезные, часто покупаемые, практичные.
Цена: от 99 до 1999 рублей.

Описание: 2–4 предложения. Подробно, но не одним предложением. Включи:
- Материал и качество
- Преимущества и применение
- Для кого подойдёт

Формат каждого элемента:
{
  "name": "Название",
  "description": "Описание 2–4 предложения.",
  "category": "Категория",
  "price": число от 99 до 1999
}

Верни ТОЛЬКО валидный JSON-массив, без markdown и пояснений."""

PROMPT_IMAGE_GENERATOR = """Товар для генерации изображения:
Название: {name}
Описание: {description}
Категория: {category}

Создай детальный промпт на АНГЛИЙСКОМ для генерации фото этого товара (Replicate).
Промпт должен:
1. Явно указать ТОЧНЫЙ тип товара и его ключевые визуальные признаки (форма, цвет, материал, размер).
2. Описать композицию: один предмет по центру, на белом/светло-сером фоне.
3. Указать стиль: профессиональная product photography, e-commerce, студийное освещение.
4. Подчеркнуть: изображение должно быть МАКСИМАЛЬНО РЕАЛИСТИЧНЫМ — как настоящая фотография реального товара, без артефактов и искажений.
5. КРИТИЧНО для товаров с дисплеем/экраном/табло (термометр, весы, часы, пульт): явно указать «clear readable digits», «LCD display showing 36.6 or 00.0», «no symbols, no random characters, no garbled text». Цифры должны быть реалистичными: 36.6 для градусника, 0.00 для весов — или «blank display» если экран выключен. Запретить: fake symbols, illegible characters, placeholder text.
6. Быть 2–4 предложения, без лишних слов. Только визуальное описание.

Верни ТОЛЬКО текст промпта, без кавычек и пояснений."""


def _parse_products_json(raw: str) -> list[dict[str, Any]]:
    """Parse GPT response to list of product dicts."""
    raw = raw.strip()
    if raw.startswith("```"):
        lines = raw.split("\n")
        start = 0
        end = len(lines)
        for i, line in enumerate(lines):
            if line.strip().startswith("```"):
                if start == 0:
                    start = i + 1
                else:
                    end = i
                    break
        raw = "\n".join(lines[start:end])
    data = json.loads(raw)
    if not isinstance(data, list):
        data = [data]
    return data[:PRODUCTS_COUNT]


def _popularity_score(price: float) -> float:
    if price <= 0:
        return 0.0
    if price < 500:
        return 1.0
    if price <= 800:
        return 0.5
    return 0.2


class MarketplaceImportService:
    """Import products from marketplace (GPT + Replicate)."""

    def __init__(self, repository: ProductRepository):
        self.repository = repository

    async def import_from_marketplace(self) -> dict[str, Any]:
        """
        Generate 5 products via GPT, generate images via Replicate, save to DB.
        Returns: imported, errors.
        """
        ai = get_ai_provider()
        raw = await ai.generate_text(PROMPT_PRODUCTS)
        items = _parse_products_json(raw)
        imported = 0
        errors: list[str] = []

        for i, item in enumerate(items):
            try:
                name = str(item.get("name") or "").strip()
                if not name:
                    errors.append(f"Товар {i + 1}: пустое название")
                    continue

                price_val = item.get("price")
                try:
                    price = float(price_val) if price_val is not None else 0.0
                except (TypeError, ValueError):
                    price = 0.0
                if price <= 0:
                    errors.append(f"Товар {i + 1}: неверная цена")
                    continue

                description = str(item.get("description") or "").strip() or None
                category = str(item.get("category") or "").strip() or None
                popularity = _popularity_score(price)
                product_id = uuid.uuid4()
                marketplace_url = f"https://marketplace.example/product/{product_id}"

                if i > 0:
                    delay = get_settings().REPLICATE_DELAY_SECONDS
                    await asyncio.sleep(delay)

                image_prompt_raw = await ai.generate_text(
                    PROMPT_IMAGE_GENERATOR.format(
                        name=name,
                        description=description or name,
                        category=category or "Товар для дома",
                    )
                )
                image_prompt = (
                    image_prompt_raw.strip()
                    + ". Professional product photography, white background, "
                    "soft studio lighting, centered, sharp focus, 8k, ultra realistic, "
                    "hyperrealistic, maximum photorealism, like a real product photo."
                )
                image_bytes = await generate_image_replicate(image_prompt)

                product = Product(
                    id=product_id,
                    name=name,
                    description=description,
                    category=category,
                    price=price,
                    popularity_score=popularity,
                    marketplace_url=marketplace_url,
                    image_filename=None,
                    image_data=image_bytes,
                )
                await self.repository.create(product)
                imported += 1
                log.info("Imported product: %s", name)

            except Exception as e:
                log.exception("Failed to import product %d: %s", i + 1, e)
                errors.append(f"Товар {i + 1}: {str(e)}")

        return {"imported": imported, "errors": errors}
