from __future__ import annotations

import json
from pathlib import PurePosixPath
import sys
from typing import Any


TRACKED_TOOLS = {"Write", "Edit", "MultiEdit"}
IGNORED_PREFIXES = (
    ".aicore/",
    ".git/",
    ".pytest_cache/",
    "__pycache__/",
)


def _normalize_path(path_text: str) -> str:
    normalized = path_text.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return PurePosixPath(normalized).as_posix()


def _extract_file_paths(payload: dict[str, Any]) -> list[str]:
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        return []

    file_path = tool_input.get("file_path")
    if isinstance(file_path, str) and file_path.strip():
        return [_normalize_path(file_path)]

    return []


def _should_ignore(path_text: str) -> bool:
    return any(
        path_text == prefix.rstrip("/") or path_text.startswith(prefix)
        for prefix in IGNORED_PREFIXES
    )


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        return 0

    if payload.get("tool_name") not in TRACKED_TOOLS:
        return 0

    changed_paths = [path for path in _extract_file_paths(payload) if not _should_ignore(path)]
    if not changed_paths:
        return 0

    joined_paths = ", ".join(changed_paths)
    print(
        "aicore 主动保存提醒：刚刚修改了文件 "
        f"{joined_paths}。请在继续下一步前运行 /aicore-save，"
        "完成 log-write + checkpoint；只有计划项完成后，才按已批准 plan/brief 运行 /aicore-ledger。",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
