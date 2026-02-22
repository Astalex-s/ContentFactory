"""Task status router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.generated_content import TaskResponse

router = APIRouter(prefix="/tasks", tags=["tasks"])

# Shared with content router
from app.routers.content import _task_store  # noqa: E402


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str) -> TaskResponse:
    """Get task status."""
    if task_id not in _task_store:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    t = _task_store[task_id]
    return TaskResponse(task_id=task_id, status=t["status"])
