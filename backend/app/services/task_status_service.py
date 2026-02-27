"""Task status tracking service for async operations (MVP: in-memory).
For production, replace with Redis or database."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

log = logging.getLogger(__name__)


class TaskStatusService:
    """In-memory task status storage with asyncio.Lock for concurrent safety."""

    def __init__(self) -> None:
        self._store: dict[str, dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def set_status(
        self,
        task_id: str,
        status: str,
        progress: int = 0,
        message: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update task status."""
        async with self._lock:
            self._store[task_id] = {
                "status": status,
                "progress": progress,
                "message": message,
                "error": error,
            }
        log.debug("Task %s: %s (progress=%d)", task_id, status, progress)

    async def get_status(self, task_id: str) -> dict[str, Any] | None:
        """Get task status. Returns None if not found."""
        async with self._lock:
            return self._store.get(task_id)

    async def delete_status(self, task_id: str) -> None:
        """Remove task status."""
        async with self._lock:
            self._store.pop(task_id, None)

    async def clear_all(self) -> None:
        """Clear all task statuses."""
        async with self._lock:
            self._store.clear()


_task_status_service = TaskStatusService()


def get_task_status_service() -> TaskStatusService:
    """Get task status service singleton."""
    return _task_status_service
