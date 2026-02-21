"""OpenAI provider implementation."""

import logging
from typing import Optional

from openai import AsyncOpenAI

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

    async def generate_text(self, prompt: str, system_prompt: str | None = None) -> str:
        """
        Generate text via OpenAI Chat Completions API.

        Args:
            prompt: User prompt.
            system_prompt: Optional system instructions.

        Returns:
            Generated text content.

        Raises:
            TimeoutError: On request timeout.
            Exception: On API errors.
        """
        max_retries = 2
        last_error: Optional[Exception] = None

        messages: list[dict] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        for attempt in range(max_retries + 1):
            try:
                response = await self._client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    timeout=float(self._timeout),
                )
                content = response.choices[0].message.content
                if content is None:
                    raise ValueError("Empty response from OpenAI")
                return content.strip()
            except Exception as e:
                last_error = e
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
