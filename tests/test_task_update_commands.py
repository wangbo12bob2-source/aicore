from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

import aicore.task_service as task_service
from aicore.cli import main
from aicore.task_update_service import update_task


class _FixedDateTime:
    value = datetime(2026, 5, 25, 9, 0, tzinfo=timezone.utc)

    @classmethod
    def now(cls):
        return cls.value


def _freeze_task_clock(monkeypatch) -> None:
    monkeypatch.setattr(task_service, "datetime", _FixedDateTime)


def _read_task(workspace: Path, task_id: str) -> dict:
    task_file = workspace / ".aicore" / "tasks" / task_id / "task.yaml"
    return yaml.safe_load(task_file.read_text(encoding="utf-8"))


def _latest_task_id(workspace: Path) -> str:
    task_root = workspace / ".aicore" / "tasks"
    return sorted(path.name for path in task_root.iterdir() if path.is_dir())[-1]


def test_update_task_persists_review_fields_and_paths(workspace: Path):
    main(["start", "实现 JWT 登录"])
    task_id = _latest_task_id(workspace)

    task = update_task(
        task_id,
        workspace,
        main_entrypoints=["API: POST /auth/login"],
        allowed_files=["src\\auth\\login.ts"],
        baseline_refs=["tests/test_auth.py"],
        success_criteria=["登录成功路径通过"],
        assumptions=["当前只有单 API 入口"],
        risks=["异常路径回归尚未补齐"],
        review_summary="主入口、修改范围、验收依据已确认",
        rollback_plan="回滚到上一版登录逻辑",
        dual_write_required=False,
        dual_write_reason="当前仅改 API 主入口。",
        now=datetime(2026, 5, 25, 10, 0, tzinfo=timezone.utc),
    )

    saved = _read_task(workspace, task["id"])

    assert saved["entrypoints"]["main"] == ["API: POST /auth/login"]
    assert saved["change_scope"]["allowed_files"] == ["src/auth/login.ts"]
    assert saved["acceptance"]["baseline_refs"] == ["tests/test_auth.py"]
    assert saved["acceptance"]["success_criteria"] == ["登录成功路径通过"]
    assert saved["review"]["summary"] == "主入口、修改范围、验收依据已确认"
    assert saved["history"]["updated_at"] == "2026-05-25T10:00:00+00:00"


def test_update_task_rejects_allowed_files_outside_workspace(workspace: Path):
    main(["start", "实现 JWT 登录"])
    task_id = _latest_task_id(workspace)

    with pytest.raises(ValueError):
        update_task(
            task_id,
            workspace,
            allowed_files=["../outside.py"],
        )


def test_approve_requires_review_ready_fields(workspace: Path, monkeypatch, capsys):
    _freeze_task_clock(monkeypatch)
    assert main(["start", "实现 JWT 登录"]) == 0

    exit_code = main(["approve", "task-2026-05-25-001", "--by", "alice"])
    captured = capsys.readouterr()

    task = _read_task(workspace, "task-2026-05-25-001")

    assert exit_code == 2
    assert task["status"] == "draft"
    assert "aicore checklist task-2026-05-25-001" in captured.err
    assert "任务级架构审核" in captured.err


def test_checklist_reports_missing_contract_items(workspace: Path, capsys):
    assert main(["start", "实现 JWT 登录"]) == 0
    task_id = _latest_task_id(workspace)

    exit_code = main(["checklist", task_id])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "任务级架构与审批检查" in captured.out
    assert "[ ] 主入口已确认" in captured.out
    assert "[OK] 任务级架构假设已说明" in captured.out
    assert "当前任务还没完成任务级架构审核" in captured.out


def test_checklist_reports_ready_after_update(workspace: Path, monkeypatch, capsys):
    _freeze_task_clock(monkeypatch)
    assert main(["start", "实现 JWT 登录"]) == 0
    assert (
        main(
            [
                "update",
                "task-2026-05-25-001",
                "--main-entrypoint",
                "API: POST /auth/login",
                "--allowed-file",
                "src/auth/login.ts",
                "--baseline-ref",
                "tests/test_auth.py",
                "--success-criteria",
                "登录成功路径通过",
                "--assumption",
                "当前只有单 API 入口",
                "--risk",
                "异常路径回归尚未补齐",
                "--review-summary",
                "主入口、修改范围、验收依据已确认",
                "--rollback-plan",
                "回滚到上一版登录逻辑",
                "--dual-write-required",
                "false",
                "--dual-write-reason",
                "当前仅改 API 主入口。",
            ]
        )
        == 0
    )

    exit_code = main(["checklist", "task-2026-05-25-001"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "[OK] 主入口已确认" in captured.out
    assert "[OK] 任务级架构假设已说明" in captured.out
    assert "已完成任务级架构审核" in captured.out


def test_approve_succeeds_after_update_fills_required_fields(
    workspace: Path, monkeypatch
):
    _freeze_task_clock(monkeypatch)
    assert main(["start", "实现 JWT 登录"]) == 0

    assert (
        main(
            [
                "update",
                "task-2026-05-25-001",
                "--main-entrypoint",
                "API: POST /auth/login",
                "--allowed-file",
                "src/auth/login.ts",
                "--baseline-ref",
                "tests/test_auth.py",
                "--success-criteria",
                "登录成功路径通过",
                "--assumption",
                "当前只有单 API 入口",
                "--risk",
                "异常路径回归尚未补齐",
                "--review-summary",
                "主入口、修改范围、验收依据已确认",
                "--rollback-plan",
                "回滚到上一版登录逻辑",
                "--dual-write-required",
                "false",
                "--dual-write-reason",
                "当前仅改 API 主入口。",
            ]
        )
        == 0
    )

    exit_code = main(["approve", "task-2026-05-25-001", "--by", "alice"])

    task = _read_task(workspace, "task-2026-05-25-001")

    assert exit_code == 0
    assert task["status"] == "approved"
    assert task["review"]["approved_by"] == "alice"
