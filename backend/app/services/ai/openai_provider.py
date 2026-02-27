"""OpenAI provider implementation."""

import logging
import time
from typing import Optional

from openai import AsyncOpenAI

from app.core.ai_logging import log_ai_error, log_ai_request, measure_ai_duration
from app.core.config import get_settings
from app.services.ai.base_ai_provider import AIProvider

log = logging.getLogger(__name__)


class OpenAIProvider(AIProvider):
    """OpenAI API implementation of AIProvider."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        timeout: Optional[int] = None,
    ) -> None:
        settings = get_settings()
        self._client = AsyncOpenAI(
            api_key=api_key or settings.OPENAI_API_KEY or None,
        )
        self._model = model or settings.OPENAI_MODEL
        self._timeout = timeout if timeout is not None else settings.AI_TIMEOUT

    async def generate_text(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        extra_context: Optional[dict] = None,
    ) -> str:
        """
        Generate text via OpenAI Chat Completions API.

        Args:
            prompt: User prompt.
            system_prompt: Optional system instructions.
            extra_context: Optional context for logging (e.g. product_id).

        Returns:
            Generated text content.

        Raises:
            TimeoutError: On request timeout.
            Exception: On API errors.
        """
        max_retries = 2
        last_error: Optional[Exception] = None
        product_id = extra_context.get("product_id") if extra_context else None

        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(max_retries + 1):
            try:
                t0 = measure_ai_duration()
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    timeout=float(self._timeout),
                )
                duration_ms = (time.perf_counter() - t0) * 1000
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("Empty response from OpenAI")

                tokens = None
                if response.usage:
                    tokens = getattr(
                        response.usage,
                        "total_tokens",
                        getattr(response.usage, "input_tokens", 0)
                        + getattr(response.usage, "output_tokens", 0),
                    )

                log_ai_request(
                    product_id=product_id,
                    model=self._model,
                    duration_ms=round(duration_ms, 2),
                    tokens=tokens,
                    status="success",
                )
                return content.strip()
            except Exception as e:
                last_error = e
                log_ai_error(
                    f"OpenAI request failed (attempt {attempt + 1}/{max_retries + 1}): {e}",
                    product_id=product_id,
                    model=self._model,
                    exc_info=False,
                )
                log.warning(
                    "OpenAI request failed (attempt %d/%d): %s",
                    attempt + 1,
                    max_retries + 1,
                    str(e),
                )
                if attempt < max_retries:
                    continue
                log.error("OpenAI generate_text failed after retries: %s", str(e))
                raise last_error from e

        raise last_error or RuntimeError("Unexpected error in generate_text")
