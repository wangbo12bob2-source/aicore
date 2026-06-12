from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from pathlib import Path

from aicore.draft_builder import DraftContext, build_draft
from aicore.state_machine import transition
from aicore.task_store import (
    load_task,
    next_task_id,
    overwrite_task,
    overwrite_tasks,
    save_task,
)
from aicore.task_update_service import validate_task_for_approval


def _resolve_current_time(now: datetime | None) -> datetime:
    current_time = now if now is not None else datetime.now()
    if current_time.tzinfo is None:
        return current_time.astimezone()
    return current_time


def start_task(
    request: str,
    cwd: Path,
    supersedes: str | None = None,
    now: datetime | None = None,
) -> dict:
    current_time = _resolve_current_time(now)
    task_id = next_task_id(cwd, current_time.date())
    task = build_draft(
        DraftContext(
            request=request,
            task_id=task_id,
            now=current_time,
            cwd=cwd,
            supersedes=supersedes,
        )
    )
    save_task(cwd, task)
    return task


def review_task(
    task_id: str,
    cwd: Path,
    now: datetime | None = None,
) -> dict:
    current_time = _resolve_current_time(now)
    task = load_task(cwd, task_id)
    if task["status"] == "reviewing":
        return task

    transition(task, "reviewing")
    task["history"]["updated_at"] = current_time.isoformat()
    overwrite_task(cwd, task)
    return task


def approve_task(
    task_id: str,
    approved_by: str,
    cwd: Path,
    now: datetime | None = None,
) -> dict:
    current_time = _resolve_current_time(now)
    task = load_task(cwd, task_id)
    transition(task, "approved")
    validate_task_for_approval(task_id, cwd)
    superseded_task: dict | None = None
    rollback_tasks: list[dict] = []
    tasks_to_write: list[dict] = []

    supersedes_task_id = task["history"]["supersedes"]
    if supersedes_task_id is not None:
        superseded_task = load_task(cwd, supersedes_task_id)
        rollback_tasks.append(deepcopy(superseded_task))
        transition(superseded_task, "superseded")
        superseded_task["history"]["superseded_by"] = task["id"]
        superseded_task["history"]["updated_at"] = current_time.isoformat()
        tasks_to_write.append(superseded_task)

    rollback_tasks.append(deepcopy(task))
    task["review"]["approved_by"] = approved_by
    task["review"]["approved_at"] = current_time.isoformat()
    task["review"]["rejected_reason"] = None
    task["history"]["updated_at"] = current_time.isoformat()
    tasks_to_write.append(task)

    if len(tasks_to_write) == 1:
        overwrite_task(cwd, task)
    else:
        overwrite_tasks(cwd, tasks_to_write, rollback_tasks=rollback_tasks)
    return task


def reject_task(
    task_id: str,
    reason: str,
    cwd: Path,
    now: datetime | None = None,
) -> dict:
    current_time = _resolve_current_time(now)
    task = load_task(cwd, task_id)
    transition(task, "rejected")
    task["review"]["rejected_reason"] = reason
    task["history"]["updated_at"] = current_time.isoformat()
    overwrite_task(cwd, task)
    return task
