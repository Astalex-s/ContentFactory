"""Task status tracking service for async operations (MVP: in-memory).
For production, use Redis or database."""

from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)


class TaskStatusService:
    """In-memory task status storage. Thread-safe for single-process deployment."""

    def __init__(self):
        self._store: dict[str, dict[str, Any]] = {}

    def set_status(
        self,
        task_id: str,
        status: str,
        progress: int = 0,
        message: str | None = None,
        error: str | None = None,
    ) -> None:
        """Update task status."""
        self._store[task_id] = {
            "status": status,
            "progress": progress,
            "message": message,
            "error": error,
        }
        log.debug("Task %s: %s (progress=%d)", task_id, status, progress)

    def get_status(self, task_id: str) -> dict[str, Any] | None:
        """Get task status. Returns None if not found."""
        return self._store.get(task_id)

    def delete_status(self, task_id: str) -> None:
        """Remove task status."""
        self._store.pop(task_id, None)

    def clear_all(self) -> None:
        """Clear all task statuses (for testing)."""
        self._store.clear()


# Singleton instance for MVP
_task_status_service = TaskStatusService()


def get_task_status_service() -> TaskStatusService:
    """Get task status service instance."""
    return _task_status_service
