"""Recommendation service for AI-based content and timing recommendations."""

from __future__ import annotations

import json
import logging
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.repositories.analytics import AnalyticsRepository
from app.repositories.generated_content import GeneratedContentRepository
from app.repositories.product import ProductRepository

log = logging.getLogger(__name__)


class RecommendationService:
    """Service for AI-powered recommendations."""

    def __init__(
        self,
        analytics_repo: AnalyticsRepository,
        content_repo: GeneratedContentRepository,
        product_repo: ProductRepository,
    ):
        self.analytics_repo = analytics_repo
        self.content_repo = content_repo
        self.product_repo = product_repo
        self.settings = get_settings()

    async def get_content_recommendations(self, content_id: UUID) -> dict:
        """Get AI recommendations for content optimization."""
        content = await self.content_repo.get_by_id(content_id)
        if not content:
            raise ValueError("Content not found")

        product = await self.product_repo.get_by_id(content.product_id)
        if not product:
            raise ValueError("Product not found")

        metrics = await self.analytics_repo.get_latest_metrics_by_content(content_id)

        views = metrics.views if metrics else 0
        clicks = metrics.clicks if metrics else 0
        ctr = metrics.ctr if metrics else 0.0

        prompt = f"""Дан контент для продукта и его метрики. Дай 3-5 кратких рекомендаций по улучшению охвата и вовлечённости.

Контент:
- Название продукта: {product.name}
- Описание продукта: {product.description[:200]}
- Платформа: {content.platform.value}
- Текст контента: {content.content_text[:300] if content.content_text else 'Нет текста'}

Метрики:
- Просмотры: {views}
- Клики: {clicks}
- CTR: {ctr:.2f}%

Верни рекомендации в формате JSON:
{{"recommendations": ["рекомендация 1", "рекомендация 2", ...], "score": 75.5}}

score — оценка текущего контента от 0 до 100.
"""

        try:
            response = await self._call_openai(prompt)
            data = json.loads(response)
            return {
                "content_id": str(content_id),
                "recommendations": data.get("recommendations", []),
                "score": data.get("score", 50.0),
            }
        except Exception as e:
            log.error("Failed to get content recommendations: %s", e)
            return {
                "content_id": str(content_id),
                "recommendations": [
                    "Не удалось получить рекомендации от AI",
                    f"Ошибка: {str(e)[:100]}",
                ],
                "score": 0.0,
            }

    async def get_publish_time_recommendations(
        self, platform: str, category: str | None = None
    ) -> dict:
        """Get AI recommendations for publish time."""
        category_text = f"для категории {category}" if category else ""
        prompt = f"""Дай 2-3 рекомендуемых временных слота для публикации контента в {platform} {category_text}.

Верни ответ в формате JSON:
{{"recommended_times": ["Понедельник 14:00-16:00", "Среда 10:00-12:00"], "reasoning": "краткое объяснение"}}
"""

        try:
            response = await self._call_openai(prompt)
            data = json.loads(response)
            return {
                "platform": platform,
                "recommended_times": data.get("recommended_times", []),
                "reasoning": data.get("reasoning", ""),
            }
        except Exception as e:
            log.error("Failed to get publish time recommendations: %s", e)
            return {
                "platform": platform,
                "recommended_times": ["Вторник 14:00-16:00", "Четверг 10:00-12:00"],
                "reasoning": "Рекомендации по умолчанию (ошибка AI)",
            }

    async def get_general_recommendations(self) -> dict:
        """Get general AI recommendations for dashboard."""
        # Get recent content and products stats
        try:
            recent_content = await self.content_repo.get_all(page=1, page_size=5)
            products_count = len(await self.product_repo.get_all(page=1, page_size=100))

            prompt = f"""Ты эксперт по контент-маркетингу. У нас есть система управления контентом.

Текущая статистика:
- Количество продуктов: {products_count}
- Недавно созданного контента: {len(recent_content)}

Дай 3-4 общих рекомендации по улучшению контент-стратегии и работы с продуктами.

Верни ответ в формате JSON:
{{
  "recommendations": [
    {{"id": "1", "title": "Заголовок", "description": "Описание", "confidence": 85}},
    {{"id": "2", "title": "Заголовок", "description": "Описание", "confidence": 75}}
  ]
}}

confidence — уровень уверенности от 0 до 100.
"""

            response = await self._call_openai(prompt)
            # Try to extract JSON from response (might be wrapped in markdown code blocks)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            data = json.loads(response)
            return {"recommendations": data.get("recommendations", [])}
        except Exception as e:
            log.error("Failed to get general recommendations: %s", e)
            if "response" in locals():
                log.error("Response was: %s", response[:500])
            return {
                "recommendations": [
                    {
                        "id": "1",
                        "title": "Увеличьте частоту публикаций",
                        "description": "Регулярные публикации помогут удержать аудиторию и улучшить охват",
                        "confidence": 80,
                    },
                    {
                        "id": "2",
                        "title": "Анализируйте метрики",
                        "description": "Отслеживайте CTR и вовлечённость для оптимизации контента",
                        "confidence": 75,
                    },
                ]
            }

    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API."""
        api_key = self.settings.OPENAI_API_KEY
        model = self.settings.OPENAI_MODEL

        if not api_key:
            raise ValueError("OPENAI_API_KEY not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "Ты эксперт по маркетингу и контенту для соцсетей. Отвечай кратко и по делу.",
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.7,
            "max_completion_tokens": 500,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers=headers,
                json=payload,
            )
            if resp.status_code != 200:
                error_detail = resp.text
                log.error(f"OpenAI API error {resp.status_code}: {error_detail}")
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            return content.strip()
