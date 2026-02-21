"""Prompt building logic for AI text generation."""

from typing import Any


SYSTEM_PROMPT = """Ты — маркетолог, создающий короткие посты для соцсетей и видеоплатформ.

ПРАВИЛА:
1. Используй ТОЛЬКО характеристики из описания товара. Не придумывай свойства, цифры, отзывы.
2. Максимум 800 символов на весь пост.
3. Формат: короткое видео (до 60 сек) — текст должен быть динамичным и цепляющим.
4. Учитывай маркетплейс: товар можно купить по ссылке.

СТРУКТУРА ОТВЕТА (соблюдай порядок):
- Hook: первая строка, цепляющая внимание (1 предложение).
- Основной текст: 2–3 предложения о товаре.
- 3 буллет-преимущества (каждый с новой строки, начинай с • или -).
- CTA: призыв к действию (перейти по ссылке, купить, заказать).
- Хештеги: 3–5 релевантных (в конце).

Ответь только текстом поста, без пояснений."""


def build_product_prompt(
    product: dict[str, Any],
    platform: str,
    tone: str,
) -> tuple[str, str]:
    """
    Build system and user prompts for product content generation.

    Args:
        product: Product data (name, description, category, price, etc.).
        platform: Target platform (youtube, vk, rutube).
        tone: Tone (neutral, emotional, expert).

    Returns:
        Tuple of (system_prompt, user_prompt).
    """
    name = product.get("name", "")
    description = product.get("description", "") or ""
    category = product.get("category", "") or ""
    price = product.get("price")

    price_str = f"{price:.0f} ₽" if price is not None else "не указана"
    desc = description[:500] if description else "—"

    price_context = ""
    if price is not None:
        if price <= 1000:
            price_context = " Товар до 1000₽ — акцент на доступность."
        else:
            price_context = " Товар премиум-сегмента — акцент на ценность."

    tone_map = {
        "neutral": "нейтральный, информативный",
        "emotional": "эмоциональный, вовлекающий",
        "expert": "экспертный, убедительный",
    }
    tone_desc = tone_map.get(tone, tone)

    platform_map = {
        "youtube": "YouTube Shorts",
        "vk": "ВКонтакте",
        "rutube": "Rutube",
    }
    platform_desc = platform_map.get(platform, platform)

    user_prompt = (
        f"Сгенерируй пост для товара.\n\n"
        f"ТОВАР:\n"
        f"- Название: {name}\n"
        f"- Категория: {category}\n"
        f"- Цена: {price_str}\n"
        f"- Описание:\n{desc}\n\n"
        f"КОНТЕКСТ:\n"
        f"- Платформа: {platform_desc}\n"
        f"- Тон: {tone_desc}\n"
        f"- Формат: короткое видео (до 60 сек)\n"
        f"- Маркетплейс: товар можно купить по ссылке.{price_context}\n\n"
        f"Сгенерируй пост по структуре: Hook → Основной текст → 3 буллета → CTA → Хештеги.\n"
        f"Максимум 800 символов. CTA обязателен."
    )

    return SYSTEM_PROMPT, user_prompt
