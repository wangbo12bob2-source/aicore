from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from pathlib import PurePosixPath, PureWindowsPath
import shutil
from uuid import uuid4


def history_root(cwd: Path) -> Path:
    return cwd / ".aicore" / "history"


def _sanitize_relative_path(path_text: str) -> str:
    return path_text.replace("\\", "__").replace("/", "__")


def _relative_text(path: Path, cwd: Path) -> str:
    return path.relative_to(cwd).as_posix()


def _prune_empty_directories(start: Path, stop: Path) -> None:
    current = start
    stop_resolved = stop.resolve()
    while current.exists() and current.resolve() != stop_resolved:
        try:
            current.rmdir()
        except OSError:
            break
        current = current.parent


def _normalize_relative_path(cwd: Path, path_text: str) -> tuple[str, Path]:
    if not path_text.strip():
        raise ValueError("文件路径不能为空")
    if PureWindowsPath(path_text).is_absolute() or PureWindowsPath(path_text).drive:
        raise ValueError("文件路径必须位于当前工作区内")

    normalized_text = path_text.replace("\\", "/")
    pure_path = PurePosixPath(normalized_text)
    if pure_path.is_absolute() or ".." in pure_path.parts:
        raise ValueError("文件路径必须位于当前工作区内")

    relative_path = PurePosixPath(*pure_path.parts).as_posix()
    cwd_resolved = cwd.resolve()
    source = (cwd_resolved / Path(*pure_path.parts)).resolve()
    try:
        source.relative_to(cwd_resolved)
    except ValueError as exc:
        raise ValueError("文件路径必须位于当前工作区内") from exc
    return relative_path, source


def _event_path(cwd: Path, event_id: str) -> Path:
    return history_root(cwd) / "events" / f"{event_id}.json"


def load_event_record(cwd: Path, event_id: str) -> dict:
    event_path = _event_path(cwd, event_id)
    if not event_path.exists():
        raise FileNotFoundError(event_id)
    return json.loads(event_path.read_text(encoding="utf-8"))


def create_event_record(
    cwd: Path,
    task_id: str,
    session_id: str,
    files: list[str],
    summary: str,
) -> dict:
    timestamp = datetime.now(timezone.utc)
    event_id = f"event-{timestamp.strftime('%Y%m%d%H%M%S%f')}-{uuid4().hex[:8]}"
    event_files: list[dict] = []
    resolved_files: list[tuple[str, Path]] = []

    for relative_path in files:
        normalized_path, source = _normalize_relative_path(cwd, relative_path)
        if not source.exists():
            raise FileNotFoundError(normalized_path)
        resolved_files.append((normalized_path, source))

    event = {
        "event_id": event_id,
        "task_id": task_id,
        "session_id": session_id,
        "timestamp": timestamp.isoformat(),
        "kind": "file_write",
        "files": event_files,
        "summary": summary,
    }

    events_dir = history_root(cwd) / "events"
    snapshots_root = history_root(cwd) / "snapshots" / task_id
    temp_snapshot_dir = snapshots_root / f".{event_id}.tmp-{uuid4().hex}"
    event_path = events_dir / f"{event_id}.json"
    temp_event_path = events_dir / f".{event_id}.tmp-{uuid4().hex}.json"

    try:
        temp_snapshot_dir.mkdir(parents=True, exist_ok=False)
        for normalized_path, source in resolved_files:
            snapshot_file = temp_snapshot_dir / Path(*PurePosixPath(normalized_path).parts)
            snapshot_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, snapshot_file)
            event_files.append(
                {
                    "path": normalized_path,
                    "change_type": "modified",
                    "snapshot_path": (
                        snapshots_root / event_id / Path(*PurePosixPath(normalized_path).parts)
                    ).relative_to(cwd).as_posix(),
                }
            )

        events_dir.mkdir(parents=True, exist_ok=True)
        temp_event_path.write_text(
            json.dumps(event, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_snapshot_dir.replace(snapshots_root / event_id)
        temp_event_path.replace(event_path)
    except Exception:
        shutil.rmtree(temp_snapshot_dir, ignore_errors=True)
        temp_event_path.unlink(missing_ok=True)
        _prune_empty_directories(snapshots_root, history_root(cwd))
        raise
    return {"event": event, "event_path": _relative_text(event_path, cwd)}


def create_checkpoint_manifest(
    cwd: Path,
    task_id: str,
    event_ids: list[str],
    summary: str,
) -> dict:
    timestamp = datetime.now(timezone.utc)
    checkpoint_id = (
        f"checkpoint-{timestamp.strftime('%Y%m%d%H%M%S%f')}-{uuid4().hex[:8]}"
    )
    checkpoint = {
        "checkpoint_id": checkpoint_id,
        "task_id": task_id,
        "timestamp": timestamp.isoformat(),
        "event_ids": event_ids,
        "summary": summary,
    }

    checkpoints_root = history_root(cwd) / "checkpoints" / task_id
    checkpoint_dir = checkpoints_root / checkpoint_id
    temp_checkpoint_dir = checkpoints_root / f".{checkpoint_id}.tmp-{uuid4().hex}"
    manifest_path = checkpoint_dir / "manifest.json"
    temp_manifest_path = temp_checkpoint_dir / "manifest.json"

    try:
        temp_checkpoint_dir.mkdir(parents=True, exist_ok=False)
        temp_manifest_path.write_text(
            json.dumps(checkpoint, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temp_checkpoint_dir.replace(checkpoint_dir)
    except Exception:
        shutil.rmtree(temp_checkpoint_dir, ignore_errors=True)
        _prune_empty_directories(checkpoints_root, history_root(cwd))
        raise

    return {
        "checkpoint": checkpoint,
        "manifest_path": _relative_text(manifest_path, cwd),
    }
