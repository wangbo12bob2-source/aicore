from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

import aicore.task_service as task_service
import aicore.task_store as task_store
from aicore.cli import main


class _FixedDateTime:
    value = datetime(2026, 5, 25, 9, 0, tzinfo=timezone.utc)

    @classmethod
    def now(cls):
        return cls.value


def _freeze_task_clock(monkeypatch) -> None:
    monkeypatch.setattr(task_service, "datetime", _FixedDateTime)


def _set_fixed_time(year: int, month: int, day: int, hour: int) -> None:
    _FixedDateTime.value = datetime(year, month, day, hour, 0, tzinfo=timezone.utc)


def _read_task(workspace: Path, task_id: str) -> dict:
    task_file = workspace / ".aicore" / "tasks" / task_id / "task.yaml"
    return yaml.safe_load(task_file.read_text(encoding="utf-8"))


def _read_brief(workspace: Path, task_id: str) -> str:
    brief_file = workspace / ".aicore" / "tasks" / task_id / "brief.md"
    return brief_file.read_text(encoding="utf-8")


def _task_root_entries(workspace: Path) -> set[str]:
    tasks_root = workspace / ".aicore" / "tasks"
    return {path.name for path in tasks_root.iterdir()}


def test_approve_superseding_task_marks_old_task_as_superseded(
    workspace: Path, monkeypatch
):
    _freeze_task_clock(monkeypatch)

    _set_fixed_time(2026, 5, 24, 9)
    assert main(["start", "实现 JWT 登录"]) == 0
    old_task_id = "task-2026-05-24-001"

    _set_fixed_time(2026, 5, 24, 10)
    assert main(["approve", old_task_id, "--by", "alice"]) == 0

    _set_fixed_time(2026, 5, 25, 9)
    assert (
        main(
            [
                "start",
                "补充 JWT refresh token 约束",
                "--supersedes",
                old_task_id,
            ]
        )
        == 0
    )
    new_task_id = "task-2026-05-25-001"

    _set_fixed_time(2026, 5, 25, 10)
    assert main(["review", new_task_id]) == 0

    _set_fixed_time(2026, 5, 25, 11)
    approve_exit = main(["approve", new_task_id, "--by", "bob"])

    new_task = _read_task(workspace, new_task_id)
    old_task = _read_task(workspace, old_task_id)
    old_brief = _read_brief(workspace, old_task_id)
    new_brief = _read_brief(workspace, new_task_id)

    assert approve_exit == 0
    assert new_task["status"] == "approved"
    assert new_task["history"]["supersedes"] == old_task_id
    assert new_task["history"]["updated_at"] == "2026-05-25T11:00:00+00:00"
    assert old_task["status"] == "superseded"
    assert old_task["history"]["superseded_by"] == new_task_id
    assert old_task["history"]["updated_at"] == "2026-05-25T11:00:00+00:00"
    assert "- 状态: `approved`" in new_brief
    assert "- 状态: `superseded`" in old_brief


def test_approve_superseding_task_allows_old_draft_to_be_superseded(
    workspace: Path, monkeypatch
):
    _freeze_task_clock(monkeypatch)

    _set_fixed_time(2026, 5, 24, 9)
    assert main(["start", "实现 JWT 登录"]) == 0
    old_task_id = "task-2026-05-24-001"

    _set_fixed_time(2026, 5, 25, 9)
    assert (
        main(
            [
                "start",
                "补充 JWT refresh token 约束",
                "--supersedes",
                old_task_id,
            ]
        )
        == 0
    )
    new_task_id = "task-2026-05-25-001"

    _set_fixed_time(2026, 5, 25, 10)
    approve_exit = main(["approve", new_task_id, "--by", "bob"])

    new_task = _read_task(workspace, new_task_id)
    old_task = _read_task(workspace, old_task_id)

    assert approve_exit == 0
    assert new_task["status"] == "approved"
    assert old_task["status"] == "superseded"
    assert old_task["history"]["superseded_by"] == new_task_id


def test_rejected_task_still_cannot_be_approved(
    workspace: Path, monkeypatch, capsys
):
    _freeze_task_clock(monkeypatch)

    _set_fixed_time(2026, 5, 25, 9)
    assert main(["start", "实现 JWT 登录"]) == 0
    task_id = "task-2026-05-25-001"

    _set_fixed_time(2026, 5, 25, 10)
    assert main(["reject", task_id, "--reason", "需求范围不清"]) == 0

    _set_fixed_time(2026, 5, 25, 11)
    approve_exit = main(["approve", task_id, "--by", "alice"])
    captured = capsys.readouterr()

    task = _read_task(workspace, task_id)

    assert approve_exit == 2
    assert task["status"] == "rejected"
    assert "invalid state transition" in captured.err.lower()


def test_overwrite_tasks_requires_paired_rollback_snapshots(
    workspace: Path, monkeypatch
):
    _freeze_task_clock(monkeypatch)

    _set_fixed_time(2026, 5, 24, 9)
    assert main(["start", "实现 JWT 登录"]) == 0
    assert main(["start", "实现 JWT 登录"]) == 0

    first_task = _read_task(workspace, "task-2026-05-24-001")
    second_task = _read_task(workspace, "task-2026-05-24-002")

    before_first = first_task["history"]["updated_at"]
    before_second = second_task["history"]["updated_at"]

    with pytest.raises(ValueError):
        task_store.overwrite_tasks(workspace, [first_task, second_task], rollback_tasks=[])

    with pytest.raises(ValueError):
        task_store.overwrite_tasks(
            workspace,
            [first_task, second_task],
            rollback_tasks=[first_task],
        )

    after_first = _read_task(workspace, "task-2026-05-24-001")
    after_second = _read_task(workspace, "task-2026-05-24-002")

    assert after_first["history"]["updated_at"] == before_first
    assert after_second["history"]["updated_at"] == before_second


def test_approve_superseding_task_rolls_back_if_second_write_fails(
    workspace: Path, monkeypatch
):
    _freeze_task_clock(monkeypatch)

    _set_fixed_time(2026, 5, 24, 9)
    assert main(["start", "实现 JWT 登录"]) == 0
    old_task_id = "task-2026-05-24-001"

    _set_fixed_time(2026, 5, 24, 10)
    assert main(["approve", old_task_id, "--by", "alice"]) == 0

    _set_fixed_time(2026, 5, 25, 9)
    assert (
        main(
            [
                "start",
                "补充 JWT refresh token 约束",
                "--supersedes",
                old_task_id,
            ]
        )
        == 0
    )
    new_task_id = "task-2026-05-25-001"

    before_old = _read_task(workspace, old_task_id)
    before_new = _read_task(workspace, new_task_id)
    before_entries = _task_root_entries(workspace)

    original_write_task_directory = task_store._write_task_directory
    call_count = 0

    def fail_on_second_write(target_directory: Path, task: dict) -> None:
        nonlocal call_count
        call_count += 1
        if call_count == 2:
            raise RuntimeError("simulated second write failure")
        original_write_task_directory(target_directory, task)

    monkeypatch.setattr(
        task_store,
        "_write_task_directory",
        fail_on_second_write,
    )

    _set_fixed_time(2026, 5, 25, 10)
    with pytest.raises(RuntimeError, match="simulated second write failure"):
        task_service.approve_task(
            new_task_id,
            "bob",
            workspace,
            now=_FixedDateTime.value,
        )

    after_old = _read_task(workspace, old_task_id)
    after_new = _read_task(workspace, new_task_id)
    after_entries = _task_root_entries(workspace)

    assert after_old["status"] == before_old["status"]
    assert after_old["history"] == before_old["history"]
    assert after_new["status"] == before_new["status"]
    assert after_new["history"] == before_new["history"]
    assert after_entries == before_entries
