"""Prompt building logic for AI text generation."""

from typing import Any


def _base_system_prompt(max_chars: int = 800) -> str:
    return f"""Ты — маркетолог, создающий контент для соцсетей и видеоплатформ.

ПРАВИЛА:
1. Используй ТОЛЬКО характеристики из описания товара. Не придумывай свойства, цифры, отзывы.
2. Максимум {max_chars} символов.
3. Учитывай маркетплейс: товар можно купить по ссылке.

Ответь только текстом, без пояснений."""


def build_product_prompt(
    product: dict[str, Any],
    platform: str,
    tone: str,
    content_text_type: str = "short_post",
) -> tuple[str, str]:
    """
    Build system and user prompts for product content generation.

    Args:
        product: Product data (name, description, category, price, etc.).
        platform: Target platform (youtube, vk, rutube).
        tone: Tone (neutral, emotional, expert).
        content_text_type: short_post | video_description | cta | all.

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

    base_context = (
        f"ТОВАР:\n"
        f"- Название: {name}\n"
        f"- Категория: {category}\n"
        f"- Цена: {price_str}\n"
        f"- Описание:\n{desc}\n\n"
        f"КОНТЕКСТ:\n"
        f"- Платформа: {platform_desc}\n"
        f"- Тон: {tone_desc}\n"
        f"- Маркетплейс: товар можно купить по ссылке.{price_context}\n\n"
    )

    if content_text_type == "short_post":
        system = _base_system_prompt(800)
        user = (
            base_context
            + "Сгенерируй КОРОТКИЙ ПОСТ. Структура: Hook → Основной текст → 3 буллета → CTA → Хештеги. "
            "Формат короткого видео (до 60 сек). Максимум 800 символов."
        )
    elif content_text_type == "video_description":
        system = _base_system_prompt(800)
        user = (
            base_context
            + "Сгенерируй ОПИСАНИЕ ДЛЯ ВИДЕО. Включи: цепляющее начало, ключевые моменты товара, "
            "призыв посмотреть/купить. Максимум 800 символов."
        )
    elif content_text_type == "cta":
        system = _base_system_prompt(300)
        user = (
            base_context
            + "Сгенерируй только ПРИЗЫВ К ДЕЙСТВИЮ (CTA): 1–3 коротких предложения, "
            "мотивирующих перейти по ссылке и купить. Максимум 300 символов."
        )
    else:  # all
        system = _base_system_prompt(2000)
        user = (
            base_context
            + "Сгенерируй ВСЁ ВМЕСТЕ в одном блоке. Структура (каждый блок с новой строки):\n"
            "1. КОРОТКИЙ ПОСТ (Hook, текст, 3 буллета, хештеги)\n"
            "2. ОПИСАНИЕ ВИДЕО\n"
            "3. CTA (призыв к действию)\n"
            "Максимум 2000 символов."
        )

    return system, user
