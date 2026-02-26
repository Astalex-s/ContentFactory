"""Prompt building logic for AI text generation."""

import re
from typing import Any


def build_multi_scene_prompt(product: dict[str, Any], count: int) -> str:
    """
    Build a single user prompt so that GPT returns exactly `count` different
    scene descriptions for the same product in one response.
    Each scene must be clearly distinct (environment, lighting, context).
    """
    name = product.get("name", "")
    description = product.get("description", "") or ""
    category = product.get("category", "") or ""

    return f"""
Product name: {name}
Category: {category}
Description: {description[:400] if description else "N/A"}

Task: Generate exactly {count} DIFFERENT scene descriptions in English for an
image-to-image AI model. Each scene must show the SAME product in a different
context. The product must stay identical (shape, color, texture, proportions).
Only the environment, lighting, setting and use context change.

Rules:
- Each description must be clearly distinct from the others (different place,
  time of day, style: e.g. kitchen, living room, office, outdoor, studio).
- Vary: interior type, lighting (natural/studio/warm/cool), camera angle,
  and how the product is used or displayed.
- Write 2–4 sentences per scene. Photorealistic, commercial style.
- Output format: exactly {count} numbered items, one per line, like:
  1) First scene description here.
  2) Second scene description here.
  3) Third scene description here.

Output only the {count} numbered descriptions, nothing else.
"""


def parse_multi_scene_response(response: str, count: int) -> list[str]:
    """
    Parse GPT response containing numbered scene descriptions into a list.
    Expects format "1) ... 2) ..." or "1. ... 2. ...". Returns up to `count` items.
    """
    if not response or not response.strip():
        return []

    text = response.strip()
    # Match "N) " or "N. " at start of line or after newline
    pattern = re.compile(
        r"(?:^|\n)\s*(\d+)[).]\s*(.+?)(?=(?:\n\s*\d+[).])|\Z)",
        re.DOTALL,
    )
    matches = pattern.findall(text)
    scenes = [m[1].strip() for m in matches if m[1].strip()]

    # Fallback: split by common numbering
    if len(scenes) < count and re.search(r"\n\s*\d+[).]\s*", text):
        parts = re.split(r"\n\s*\d+[).]\s*", text, maxsplit=count)
        scenes = [p.strip() for p in parts if p.strip()][:count]

    # If still not enough, treat whole response as one or split by double newline
    if len(scenes) < count and text:
        scenes = [s.strip() for s in text.split("\n\n") if s.strip()][:count]

    return scenes[:count]


def build_image_scene_prompt(product: dict[str, Any], scene_index: int) -> str:
    """
    Build user prompt for GPT to generate realistic use-case scenes for
    image-to-image generation.
    The product must remain EXACTLY the same (shape, color, texture, proportions).
    Only environment, lighting, interaction and context may change.

    Three different contextual lifestyle scenes are generated based on
    product purpose.
    """

    name = product.get("name", "")
    description = product.get("description", "") or ""
    category = product.get("category", "") or ""

    # Scene types cycle (0, 1, 2)
    scene_types = [
        "product_in_use",       # realistic usage scenario
        "functional_context",   # environment that highlights functionality
        "lifestyle_context",    # emotional / lifestyle marketing scene
    ]

    scene_type = scene_types[scene_index % len(scene_types)]

    return f"""
Product name: {name}
Category: {category}
Description: {description[:300] if description else "N/A"}

Generate a realistic scene description in English for an image-to-image
AI model.

CRITICAL RULES:
- The product must remain EXACTLY the same as in the original image.
- Do NOT change shape, color, texture, material, proportions, branding
  or number of items.
- Do NOT redesign or reinterpret the product.
- Only change environment, lighting, camera angle, and interaction context.

Scene type: {scene_type}

Instructions:
If the product is a device or tool, show it being naturally used
according to its real-world purpose.
If the product is wearable, show it in a natural human context.
If the product is home-related, place it in a realistic home environment.

Create a vivid, photorealistic commercial scene.
Describe lighting, atmosphere, camera framing and interaction.
Output 3–4 sentences in English.
Only output the scene description.
"""


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
        platform: Target platform (youtube, vk, tiktok).
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
        "tiktok": "TikTok",
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
