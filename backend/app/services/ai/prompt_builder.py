"""Prompt building logic for AI text generation."""

from typing import Any


def build_product_prompt(
    product: dict[str, Any],
    platform: str,
    tone: str,
) -> str:
    """
    Build prompt for product content generation.

    Args:
        product: Product data (name, description, category, price, etc.).
        platform: Target platform (youtube, vk, rutube).
        tone: Tone (neutral, emotional, expert).

    Returns:
        Formatted prompt string.
    """
    name = product.get("name", "")
    description = product.get("description", "") or ""
    category = product.get("category", "") or ""
    price = product.get("price")

    price_str = f"{price:.0f} ₽" if price is not None else "не указана"
    desc = description[:500] if description else "—"

    return (
        f"Сгенерируй короткий маркетинговый пост для товара.\n\n"
        f"Товар: {name}\n"
        f"Категория: {category}\n"
        f"Цена: {price_str}\n"
        f"Описание: {desc}\n\n"
        f"Платформа: {platform}\n"
        f"Тон: {tone}\n\n"
        f"Требования: до 800 символов, включи CTA."
    )
