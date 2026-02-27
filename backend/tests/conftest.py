"""Pytest fixtures."""

import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_media_dir() -> Path:
    """Temporary directory for media storage tests."""
    with tempfile.TemporaryDirectory() as d:
        yield Path(d)
