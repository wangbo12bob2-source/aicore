from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from aicore.cli import main
from aicore.task_query_service import get_task, list_tasks
from aicore.task_service import start_task


def test_list_tasks_returns_empty_when_no_tasks_exist(workspace: Path):
    assert list_tasks(workspace) == []


def test_list_tasks_returns_tasks_sorted_by_task_id(workspace: Path):
    start_task(
        "实现 JWT 登录",
        workspace,
        now=datetime(2026, 5, 24, 9, 0, tzinfo=timezone.utc),
    )
    start_task(
        "补充 JWT refresh token 约束",
        workspace,
        now=datetime(2026, 5, 25, 9, 0, tzinfo=timezone.utc),
    )

    tasks = list_tasks(workspace)

    assert [task["id"] for task in tasks] == [
        "task-2026-05-24-001",
        "task-2026-05-25-001",
    ]


def test_get_task_returns_existing_task(workspace: Path):
    task = start_task(
        "实现 JWT 登录",
        workspace,
        now=datetime(2026, 5, 24, 9, 0, tzinfo=timezone.utc),
    )

    loaded = get_task(task["id"], workspace)

    assert loaded["id"] == task["id"]
    assert loaded["request"]["raw"] == "实现 JWT 登录"


def test_cli_list_prints_empty_message_when_no_tasks_exist(workspace: Path, capsys):
    exit_code = main(["list"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert captured.out.strip() == "暂无任务"


def test_cli_show_prints_existing_task_detail(workspace: Path, capsys):
    task = start_task(
        "实现 JWT 登录",
        workspace,
        now=datetime(2026, 5, 24, 9, 0, tzinfo=timezone.utc),
    )

    exit_code = main(["show", task["id"]])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert task["id"] in captured.out
    assert "状态: draft" in captured.out
    assert "任务目录: .aicore/tasks/task-2026-05-24-001" in captured.out
