"""Task status router."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.schemas.generated_content import TaskResponse
from app.services.task_status_service import get_task_status_service

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task_status(task_id: str) -> TaskResponse:
    """Get task status."""
    task_svc = get_task_status_service()
    status_data = task_svc.get_status(task_id)
    if not status_data:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    return TaskResponse(task_id=task_id, status=status_data["status"])
