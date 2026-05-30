from __future__ import annotations

from datetime import date
import shutil
from pathlib import Path
from uuid import uuid4

import yaml

from aicore.task_views import render_brief


def tasks_root(cwd: Path) -> Path:
    return cwd / ".aicore" / "tasks"


def task_dir(cwd: Path, task_id: str) -> Path:
    return tasks_root(cwd) / task_id


def next_task_id(cwd: Path, today: date) -> str:
    root = tasks_root(cwd)
    root.mkdir(parents=True, exist_ok=True)

    prefix = f"task-{today.isoformat()}-"
    indexes: list[int] = []
    for path in root.iterdir():
        if not path.is_dir() or not path.name.startswith(prefix):
            continue
        suffix = path.name.removeprefix(prefix)
        if suffix.isdigit():
            indexes.append(int(suffix))

    return f"{prefix}{(max(indexes, default=0) + 1):03d}"


def _write_task_directory(target_directory: Path, task: dict) -> None:
    root = target_directory.parent
    temp_directory = root / f".{task['id']}.tmp-{uuid4().hex}"
    temp_directory.mkdir(parents=True, exist_ok=False)

    try:
        task_text = yaml.safe_dump(task, allow_unicode=True, sort_keys=False)
        (temp_directory / "task.yaml").write_text(task_text, encoding="utf-8")
        (temp_directory / "brief.md").write_text(render_brief(task), encoding="utf-8")
        if target_directory.exists():
            backup_directory = root / f".{task['id']}.bak-{uuid4().hex}"
            target_directory.replace(backup_directory)
            try:
                temp_directory.replace(target_directory)
            except Exception:
                if backup_directory.exists():
                    backup_directory.replace(target_directory)
                raise
            else:
                shutil.rmtree(backup_directory, ignore_errors=True)
        else:
            temp_directory.replace(target_directory)
    except Exception:
        shutil.rmtree(temp_directory, ignore_errors=True)
        raise


def load_task(cwd: Path, task_id: str) -> dict:
    task_file = task_dir(cwd, task_id) / "task.yaml"
    return yaml.safe_load(task_file.read_text(encoding="utf-8"))


def save_task(cwd: Path, task: dict) -> None:
    root = tasks_root(cwd)
    root.mkdir(parents=True, exist_ok=True)

    directory = task_dir(cwd, task["id"])
    if directory.exists():
        raise FileExistsError(directory)

    _write_task_directory(directory, task)


def overwrite_task(cwd: Path, task: dict) -> None:
    root = tasks_root(cwd)
    root.mkdir(parents=True, exist_ok=True)

    directory = task_dir(cwd, task["id"])
    if not directory.exists():
        raise FileNotFoundError(directory)

    _write_task_directory(directory, task)


def overwrite_tasks(
    cwd: Path,
    tasks: list[dict],
    rollback_tasks: list[dict] | None = None,
) -> None:
    if rollback_tasks is None or len(rollback_tasks) != len(tasks):
        raise ValueError("rollback_tasks must be provided for every task update")

    rollback_snapshots = rollback_tasks
    written_count = 0
    try:
        for task in tasks:
            overwrite_task(cwd, task)
            written_count += 1
    except Exception as exc:
        try:
            for task in reversed(rollback_snapshots[:written_count]):
                overwrite_task(cwd, task)
        except Exception as rollback_exc:
            raise RuntimeError(
                "failed to rollback task updates after partial write"
            ) from rollback_exc
        raise
