from __future__ import annotations

from pathlib import Path

from aicore.history_store import (
    create_checkpoint_manifest,
    create_event_record,
    load_event_record,
)


def log_write(
    cwd: Path,
    task_id: str,
    session_id: str,
    files: list[str],
    summary: str,
) -> dict:
    if not files:
        raise ValueError("files 不能为空")
    if not summary.strip():
        raise ValueError("summary 不能为空")

    return create_event_record(
        cwd=cwd,
        task_id=task_id,
        session_id=session_id,
        files=files,
        summary=summary.strip(),
    )


def create_checkpoint(
    cwd: Path,
    task_id: str,
    event_ids: list[str],
    summary: str,
) -> dict:
    if not event_ids:
        raise ValueError("event_ids 不能为空")
    if not summary.strip():
        raise ValueError("summary 不能为空")

    normalized_event_ids = list(event_ids)
    for event_id in normalized_event_ids:
        event = load_event_record(cwd, event_id)
        if event["task_id"] != task_id:
            raise ValueError(
                f"event {event_id} 属于 {event['task_id']}，不能用于 {task_id}"
            )

    return create_checkpoint_manifest(
        cwd=cwd,
        task_id=task_id,
        event_ids=normalized_event_ids,
        summary=summary.strip(),
    )
