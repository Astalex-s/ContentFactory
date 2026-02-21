"""Centralized AI request logging and error tracking."""

import logging
import time
from pathlib import Path
from typing import Any, Optional, Union
from uuid import UUID

# Separate logger for AI metrics
ai_logger = logging.getLogger("app.ai.requests")

# Separate file handler for AI errors
_ai_errors_logger: Optional[logging.Logger] = None


def _ensure_ai_errors_logger() -> logging.Logger:
    """Lazy init of ai_errors logger with file handler."""
    global _ai_errors_logger
    if _ai_errors_logger is None:
        _ai_errors_logger = logging.getLogger("app.ai.errors")
        _ai_errors_logger.setLevel(logging.ERROR)
        _ai_errors_logger.propagate = False
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        fh = logging.FileHandler(log_dir / "ai_errors.log", encoding="utf-8")
        fh.setFormatter(
            logging.Formatter(
                "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        _ai_errors_logger.addHandler(fh)
    return _ai_errors_logger


def log_ai_request(
    product_id: Optional[Union[UUID, str]] = None,
    model: Optional[str] = None,
    duration_ms: Optional[float] = None,
    tokens: Optional[int] = None,
    status: str = "success",
    extra: Optional[dict[str, Any]] = None,
) -> None:
    """
    Log AI request metrics.

    Args:
        product_id: Product ID if applicable.
        model: AI model name.
        duration_ms: Response time in milliseconds.
        tokens: Token count from usage.
        status: success | error | timeout.
        extra: Additional fields.
    """
    payload: dict[str, Any] = {
        "product_id": str(product_id) if product_id else None,
        "model": model,
        "duration_ms": duration_ms,
        "tokens": tokens,
        "status": status,
    }
    if extra:
        payload.update(extra)
    ai_logger.info("AI request: %s", payload)


def log_ai_error(
    message: str,
    product_id: Optional[Union[UUID, str]] = None,
    model: Optional[str] = None,
    exc_info: bool = True,
) -> None:
    """Log AI error to ai_errors.log."""
    logger = _ensure_ai_errors_logger()
    parts = [message]
    if product_id:
        parts.append(f"product_id={product_id}")
    if model:
        parts.append(f"model={model}")
    logger.error(" | ".join(parts), exc_info=exc_info)


def measure_ai_duration() -> float:
    """Return current time for duration calculation."""
    return time.perf_counter()
