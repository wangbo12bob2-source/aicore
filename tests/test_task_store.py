from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
import yaml

import aicore.task_store as task_store
from aicore.draft_builder import validate_request_scope
from aicore.task_service import start_task
from aicore.task_store import save_task


def test_save_task_does_not_silently_overwrite_existing_task(workspace: Path):
    fixed_now = datetime(2026, 5, 24, 9, 0, tzinfo=timezone.utc)
    task = start_task("实现 JWT 登录", workspace, now=fixed_now)

    task["request"]["raw"] = "这个值不应覆盖原文件"

    with pytest.raises(FileExistsError):
        save_task(workspace, task)

    saved = yaml.safe_load(
        (workspace / ".aicore" / "tasks" / task["id"] / "task.yaml").read_text(encoding="utf-8")
    )
    assert saved["request"]["raw"] == "实现 JWT 登录"


def test_start_task_accepts_injected_time_for_task_id(workspace: Path):
    fixed_now = datetime(2026, 5, 24, 9, 0, tzinfo=timezone.utc)

    task = start_task("实现 JWT 登录", workspace, now=fixed_now)

    assert task["id"] == "task-2026-05-24-001"


def test_validate_request_scope_counts_unique_subsystems_once():
    validate_request_scope("聊天 chat 报表 report")


def test_save_task_cleans_up_partial_write_and_allows_retry(
    workspace: Path, monkeypatch: pytest.MonkeyPatch
):
    task = {
        "id": "task-2026-05-24-001",
        "status": "draft",
        "request": {"raw": "实现 JWT 登录"},
        "project": {"type": "product-delivery"},
        "scope": {"module": "auth-login"},
        "entrypoints": {"main": [], "compat": []},
        "implementation": {
            "dual_write_required": False,
            "dual_write_reason": "待确认是否存在兼容入口或双实现。",
        },
        "change_scope": {"allowed_files": [], "protected_areas": ["禁止修改范围示例"]},
        "acceptance": {"baseline_refs": []},
        "context": {
            "assumptions": ["假设示例"],
            "risks": ["风险示例"],
            "rollback_plan": "回退方案示例",
        },
    }

    def fail_render_brief(_: dict) -> str:
        raise RuntimeError("render failed")

    monkeypatch.setattr(task_store, "render_brief", fail_render_brief)

    with pytest.raises(RuntimeError):
        save_task(workspace, task)

    final_dir = workspace / ".aicore" / "tasks" / task["id"]
    assert not final_dir.exists()

    monkeypatch.undo()

    save_task(workspace, task)

    assert final_dir.exists()
    assert (final_dir / "task.yaml").exists()
    assert (final_dir / "brief.md").exists()
