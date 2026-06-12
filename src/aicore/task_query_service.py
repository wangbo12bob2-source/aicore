from __future__ import annotations

from pathlib import Path

from aicore.task_store import load_task, tasks_root


def list_tasks(cwd: Path) -> list[dict]:
    root = tasks_root(cwd)
    if not root.exists():
        return []

    tasks: list[dict] = []
    for path in sorted(root.iterdir()):
        if not path.is_dir():
            continue
        tasks.append(load_task(cwd, path.name))
    return tasks


def get_task(task_id: str, cwd: Path) -> dict:
    return load_task(cwd, task_id)
