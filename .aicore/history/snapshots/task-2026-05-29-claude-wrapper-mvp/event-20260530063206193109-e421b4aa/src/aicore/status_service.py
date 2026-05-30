from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def _history_root(cwd: Path) -> Path:
    return cwd / ".aicore" / "history"


def _load_json_files(root: Path) -> list[dict[str, Any]]:
    if not root.exists():
        return []

    records: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.json")):
        records.append(json.loads(path.read_text(encoding="utf-8")))
    return records


def _event_sort_key(event: dict[str, Any]) -> tuple[str, str]:
    return (str(event.get("timestamp", "")), str(event.get("event_id", "")))


def _collect_checkpointed_event_ids(checkpoints: list[dict[str, Any]]) -> list[str]:
    event_ids: set[str] = set()
    for checkpoint in checkpoints:
        for event_id in checkpoint.get("event_ids", []):
            event_ids.add(str(event_id))
    return sorted(event_ids)


def _collect_multi_session_file_risks(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    file_events: dict[str, list[dict[str, Any]]] = {}
    for event in events:
        for file_record in event.get("files", []):
            path = str(file_record.get("path", ""))
            if path:
                file_events.setdefault(path, []).append(event)

    risks: list[dict[str, Any]] = []
    for path, related_events in sorted(file_events.items()):
        sessions = sorted({str(event.get("session_id", "")) for event in related_events})
        if len(sessions) < 2:
            continue
        risks.append(
            {
                "path": path,
                "sessions": sessions,
                "event_ids": [
                    str(event.get("event_id", ""))
                    for event in sorted(related_events, key=_event_sort_key)
                ],
            }
        )
    return risks


def build_status(cwd: Path) -> dict[str, list[Any]]:
    events = sorted(
        _load_json_files(_history_root(cwd) / "events"),
        key=_event_sort_key,
    )
    checkpoints = _load_json_files(_history_root(cwd) / "checkpoints")
    checkpointed_event_ids = _collect_checkpointed_event_ids(checkpoints)
    checkpointed_event_id_set = set(checkpointed_event_ids)

    return {
        "sessions": sorted({str(event.get("session_id", "")) for event in events}),
        "checkpointed_event_ids": checkpointed_event_ids,
        "pending_event_ids": [
            str(event.get("event_id", ""))
            for event in events
            if str(event.get("event_id", "")) not in checkpointed_event_id_set
        ],
        "multi_session_file_risks": _collect_multi_session_file_risks(events),
    }
