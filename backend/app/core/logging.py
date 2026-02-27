"""Centralized logging configuration."""

import logging
import sys

from app.core.config import get_settings


def setup_logging(log_level: str | None = None) -> None:
    """
    Configure application logging.
    Logs to stdout (12-factor app).
    """
    level = log_level or get_settings().LOG_LEVEL
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    logging.basicConfig(
        level=numeric_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )

    # Reduce noise from third-party libs
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
