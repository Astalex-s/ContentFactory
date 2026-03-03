"""TTS provider for voiceover generation."""

from __future__ import annotations

import logging
import os
import tempfile

from app.core.config import get_settings

log = logging.getLogger(__name__)


async def generate_speech(text: str) -> bytes:
    """
    Generate speech from text. Returns MP3 bytes.
    Uses OpenAI TTS when TTS_PROVIDER=openai, else returns empty bytes.
    """
    settings = get_settings()
    provider = (settings.TTS_PROVIDER or "openai").lower().strip()
    text = (text or "").strip()
    if not text:
        return b""

    if provider == "openai":
        return await _openai_tts(text, settings.OPENAI_TTS_VOICE or "alloy")
    if provider == "edge":
        return await _edge_tts(text)
    log.warning("Unknown TTS_PROVIDER=%s, skipping voiceover", provider)
    return b""


async def _openai_tts(text: str, voice: str) -> bytes:
    """OpenAI TTS API."""
    try:
        from openai import AsyncOpenAI

        client = AsyncOpenAI()
        response = await client.audio.speech.create(
            model="tts-1",
            voice=voice or "alloy",
            input=text,
        )
        return response.content
    except ImportError:
        log.warning("openai package not available for TTS")
        return b""
    except Exception as e:
        log.warning("OpenAI TTS failed: %s", e)
        return b""


async def _edge_tts(text: str) -> bytes:
    """Edge TTS (free, no API key)."""
    try:
        import edge_tts  # type: ignore[reportMissingImports]

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as tmp:
            path = tmp.name
        try:
            communicate = edge_tts.Communicate(text, "ru-RU-DmitryNeural")
            await communicate.save(path)
            with open(path, "rb") as f:
                return f.read()
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass
    except ImportError:
        log.warning("edge-tts not installed, run: pip install edge-tts")
        return b""
    except Exception as e:
        log.warning("Edge TTS failed: %s", e)
        return b""
