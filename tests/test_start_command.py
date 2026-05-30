from __future__ import annotations

from pathlib import Path

import yaml

from aicore.cli import main


def _task_dirs(workspace: Path) -> list[Path]:
    tasks_root = workspace / ".aicore" / "tasks"
    if not tasks_root.exists():
        return []
    return sorted(path for path in tasks_root.iterdir() if path.is_dir())


def test_start_creates_task_yaml_and_brief(workspace: Path, capsys):
    exit_code = main(["start", "实现 JWT 登录"])
    captured = capsys.readouterr()

    task_dirs = _task_dirs(workspace)

    assert exit_code == 0
    assert len(task_dirs) == 1

    task_file = task_dirs[0] / "task.yaml"
    brief_file = task_dirs[0] / "brief.md"

    assert task_file.exists()
    assert brief_file.exists()

    data = yaml.safe_load(task_file.read_text(encoding="utf-8"))

    assert data["status"] == "draft"
    assert data["request"]["raw"] == "实现 JWT 登录"
    assert data["project"]["type"] == "product-delivery"
    assert data["scope"]["module"] == "auth-login"
    assert data["change_scope"]["protected_areas"] != []
    assert data["context"]["assumptions"] != []
    assert data["context"]["risks"] != []
    assert data["context"]["rollback_plan"] != ""
    assert data["history"]["supersedes"] is None

    assert "项目类型" in captured.out
    assert "product-delivery" in captured.out
    assert "主入口" in captured.out
    assert "是否需要双改" in captured.out
    assert "双改原因" in captured.out
    assert "允许修改文件" in captured.out
    assert "回退方案" in captured.out

    brief_text = brief_file.read_text(encoding="utf-8")
    assert "需要人工确认后再进入下一步" in brief_text
    assert "人工确认清单" in brief_text
    assert "待确认" in brief_text
    assert "主入口" in brief_text
    assert "是否需要双改" in brief_text
    assert "双改原因" in brief_text
    assert "允许修改文件" in brief_text
    assert "禁止修改范围" in brief_text
    assert "验收依据" in brief_text
    assert "回退方案" in brief_text
    assert "否" in brief_text
    assert data["implementation"]["dual_write_reason"] in brief_text
    assert data["change_scope"]["protected_areas"][0] in brief_text
    assert data["context"]["rollback_plan"] in brief_text


def test_start_records_supersedes_reference(workspace: Path):
    exit_code = main(
        [
            "start",
            "补充 JWT refresh token 约束",
            "--supersedes",
            "task-2026-05-24-001",
        ]
    )

    task_dirs = _task_dirs(workspace)

    assert exit_code == 0
    assert len(task_dirs) == 1

    data = yaml.safe_load((task_dirs[0] / "task.yaml").read_text(encoding="utf-8"))
    assert data["history"]["supersedes"] == "task-2026-05-24-001"


def test_start_rejects_request_without_stable_single_module(workspace: Path):
    exit_code = main(["start", "优化一下现有实现"])

    assert exit_code == 2
    assert _task_dirs(workspace) == []


def test_start_rejects_broad_multi_system_request(workspace: Path):
    exit_code = main(["start", "同时重写聊天、支付、文件存储和报表系统"])

    assert exit_code == 2
    assert _task_dirs(workspace) == []


def test_start_rejects_broad_multi_system_request_without_connector(workspace: Path):
    exit_code = main(["start", "重写聊天、支付、文件存储和报表系统"])

    assert exit_code == 2
    assert _task_dirs(workspace) == []


def test_start_rejects_obvious_multi_entrypoint_risk_request(workspace: Path):
    exit_code = main(["start", "同步修改登录 SPA、嵌入式 HTML 和 Electron 壳入口"])

    assert exit_code == 2
    assert _task_dirs(workspace) == []
