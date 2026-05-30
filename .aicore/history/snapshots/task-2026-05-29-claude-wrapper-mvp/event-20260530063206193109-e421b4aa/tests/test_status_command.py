from __future__ import annotations

from pathlib import Path

from aicore.history_service import create_checkpoint, log_write
from aicore.status_service import build_status


def _write_file(workspace: Path, path_text: str, content: str) -> None:
    path = workspace / path_text
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_status_reports_sessions_pending_events_and_multi_session_file_risks(
    workspace: Path,
):
    _write_file(workspace, "README.md", "claude edit\n")
    claude_event = log_write(
        cwd=workspace,
        task_id="task-1",
        session_id="claude-20260530",
        files=["README.md"],
        summary="Claude 修改 README",
    )

    _write_file(workspace, "README.md", "codex edit\n")
    codex_event = log_write(
        cwd=workspace,
        task_id="task-1",
        session_id="codex-20260530",
        files=["README.md"],
        summary="Codex 修改 README",
    )

    _write_file(workspace, "src/app.py", "print('ok')\n")
    trae_event = log_write(
        cwd=workspace,
        task_id="task-1",
        session_id="trae-20260530",
        files=["src/app.py"],
        summary="Trae 修改 app",
    )

    create_checkpoint(
        cwd=workspace,
        task_id="task-1",
        event_ids=[claude_event["event"]["event_id"]],
        summary="Claude README 修改已稳定",
    )

    status = build_status(workspace)

    assert status["sessions"] == [
        "claude-20260530",
        "codex-20260530",
        "trae-20260530",
    ]
    assert status["checkpointed_event_ids"] == [claude_event["event"]["event_id"]]
    assert status["pending_event_ids"] == [
        codex_event["event"]["event_id"],
        trae_event["event"]["event_id"],
    ]
    assert status["multi_session_file_risks"] == [
        {
            "path": "README.md",
            "sessions": ["claude-20260530", "codex-20260530"],
            "event_ids": [
                claude_event["event"]["event_id"],
                codex_event["event"]["event_id"],
            ],
        }
    ]


def test_status_handles_empty_history(workspace: Path):
    status = build_status(workspace)

    assert status["sessions"] == []
    assert status["checkpointed_event_ids"] == []
    assert status["pending_event_ids"] == []
    assert status["multi_session_file_risks"] == []
