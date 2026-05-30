from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import yaml

import aicore.task_service as task_service
from aicore.cli import main


class _FixedDateTime:
    value = datetime(2026, 5, 25, 9, 0, tzinfo=timezone.utc)

    @classmethod
    def now(cls):
        return cls.value


def _read_task(workspace: Path, task_id: str) -> dict:
    task_file = workspace / ".aicore" / "tasks" / task_id / "task.yaml"
    return yaml.safe_load(task_file.read_text(encoding="utf-8"))


def _read_brief(workspace: Path, task_id: str) -> str:
    brief_file = workspace / ".aicore" / "tasks" / task_id / "brief.md"
    return brief_file.read_text(encoding="utf-8")


def _freeze_task_clock(monkeypatch) -> None:
    monkeypatch.setattr(task_service, "datetime", _FixedDateTime)


def _fixed_now_isoformat() -> str:
    return _FixedDateTime.value.isoformat()


def test_review_moves_draft_to_reviewing_and_rerenders_brief(
    workspace: Path, monkeypatch, capsys
):
    _freeze_task_clock(monkeypatch)
    start_exit = main(["start", "实现 JWT 登录"])
    assert start_exit == 0

    task_id = "task-2026-05-25-001"
    before_brief = _read_brief(workspace, task_id)
    assert "- 状态: `draft`" in before_brief

    exit_code = main(["review", task_id])
    captured = capsys.readouterr()

    task = _read_task(workspace, task_id)
    after_brief = _read_brief(workspace, task_id)

    assert exit_code == 0
    assert task["status"] == "reviewing"
    assert task["history"]["updated_at"] == _fixed_now_isoformat()
    assert "- 状态: `reviewing`" in after_brief
    assert after_brief != before_brief
    assert "请查看 .aicore/tasks/task-2026-05-25-001/brief.md" in captured.out
    assert "人工确认后，再决定 approve 或 reject" in captured.out


def test_review_is_idempotent_when_task_is_already_reviewing(
    workspace: Path, monkeypatch
):
    _freeze_task_clock(monkeypatch)
    start_exit = main(["start", "实现 JWT 登录"])
    assert start_exit == 0

    task_id = "task-2026-05-25-001"
    first_review_exit = main(["review", task_id])
    assert first_review_exit == 0

    first_task = _read_task(workspace, task_id)
    first_brief = _read_brief(workspace, task_id)

    second_review_exit = main(["review", task_id])

    second_task = _read_task(workspace, task_id)
    second_brief = _read_brief(workspace, task_id)

    assert second_review_exit == 0
    assert second_task["status"] == "reviewing"
    assert second_brief == first_brief
    assert second_task == first_task
    assert "- 状态: `reviewing`" in second_brief


def test_approve_allows_draft_and_reviewing_and_records_reviewer_metadata(
    workspace: Path,
    monkeypatch,
):
    _freeze_task_clock(monkeypatch)
    start_exit = main(["start", "实现 JWT 登录"])
    assert start_exit == 0

    task_id = "task-2026-05-25-001"

    exit_code = main(["approve", task_id, "--by", "alice"])

    task = _read_task(workspace, task_id)
    brief = _read_brief(workspace, task_id)

    assert exit_code == 0
    assert task["status"] == "approved"
    assert task["review"]["approved_by"] == "alice"
    assert task["review"]["approved_at"] == _fixed_now_isoformat()
    assert task["history"]["updated_at"] == _fixed_now_isoformat()
    assert task["review"]["rejected_reason"] is None
    assert "- 状态: `approved`" in brief

    start_exit = main(["start", "实现 JWT 登录"])
    assert start_exit == 0

    reviewing_task_id = "task-2026-05-25-002"
    review_exit = main(["review", reviewing_task_id])
    assert review_exit == 0

    reviewing_approve_exit = main(["approve", reviewing_task_id, "--by", "bob"])

    reviewing_task = _read_task(workspace, reviewing_task_id)

    assert reviewing_approve_exit == 0
    assert reviewing_task["status"] == "approved"
    assert reviewing_task["review"]["approved_by"] == "bob"
    assert reviewing_task["review"]["approved_at"] == _fixed_now_isoformat()
    assert reviewing_task["history"]["updated_at"] == _fixed_now_isoformat()


def test_reject_allows_draft_and_reviewing_and_records_reason(
    workspace: Path, monkeypatch
):
    _freeze_task_clock(monkeypatch)
    start_exit = main(["start", "实现 JWT 登录"])
    assert start_exit == 0

    draft_task_id = "task-2026-05-25-001"
    draft_reject_exit = main(["reject", draft_task_id, "--reason", "缺少验收标准"])

    draft_task = _read_task(workspace, draft_task_id)

    assert draft_reject_exit == 0
    assert draft_task["status"] == "rejected"
    assert draft_task["review"]["rejected_reason"] == "缺少验收标准"
    assert draft_task["history"]["updated_at"] == _fixed_now_isoformat()

    start_exit = main(["start", "实现 JWT 登录"])
    assert start_exit == 0

    reviewing_task_id = "task-2026-05-25-002"
    review_exit = main(["review", reviewing_task_id])
    assert review_exit == 0

    reviewing_reject_exit = main(
        ["reject", reviewing_task_id, "--reason", "主入口未确认"]
    )

    reviewing_task = _read_task(workspace, reviewing_task_id)

    assert reviewing_reject_exit == 0
    assert reviewing_task["status"] == "rejected"
    assert reviewing_task["review"]["rejected_reason"] == "主入口未确认"
    assert reviewing_task["history"]["updated_at"] == _fixed_now_isoformat()


def test_rejected_task_cannot_be_approved_and_returns_two(
    workspace: Path, monkeypatch, capsys
):
    _freeze_task_clock(monkeypatch)
    start_exit = main(["start", "实现 JWT 登录"])
    assert start_exit == 0

    task_id = "task-2026-05-25-001"
    reject_exit = main(["reject", task_id, "--reason", "需求范围不清"])
    assert reject_exit == 0

    exit_code = main(["approve", task_id, "--by", "alice"])
    captured = capsys.readouterr()

    task = _read_task(workspace, task_id)

    assert exit_code == 2
    assert task["status"] == "rejected"
    assert "invalid state transition" in captured.err.lower()


def test_illegal_state_transition_fails_explicitly(
    workspace: Path, monkeypatch, capsys
):
    _freeze_task_clock(monkeypatch)
    start_exit = main(["start", "实现 JWT 登录"])
    assert start_exit == 0

    task_id = "task-2026-05-25-001"
    approve_exit = main(["approve", task_id, "--by", "alice"])
    assert approve_exit == 0

    exit_code = main(["review", task_id])
    captured = capsys.readouterr()

    task = _read_task(workspace, task_id)

    assert exit_code == 2
    assert task["status"] == "approved"
    assert "invalid state transition" in captured.err.lower()


def test_missing_task_reports_task_not_found_consistently(capsys):
    exit_code = main(["approve", "task-404", "--by", "alice"])
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "task not found" in captured.err.lower()
