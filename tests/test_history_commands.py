from __future__ import annotations

import aicore.history_store as history_store
import inspect
import json
from pathlib import Path

from aicore.history_service import create_checkpoint, log_write


def test_log_write_persists_event_and_snapshots(workspace: Path):
    source_file = workspace / "src" / "auth" / "login.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const login = 'ok';\n", encoding="utf-8")

    result = log_write(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        session_id="session-1",
        files=["src/auth/login.ts"],
        summary="记录登录文件改动",
    )

    assert result["event"]["task_id"] == "task-2026-05-25-001"
    assert result["event"]["kind"] == "file_write"
    assert len(result["event"]["files"]) == 1

    event_path = workspace / result["event_path"]
    snapshot_path = workspace / result["event"]["files"][0]["snapshot_path"]

    assert event_path.exists()
    assert snapshot_path.exists()
    assert snapshot_path.read_text(encoding="utf-8") == "export const login = 'ok';\n"


def test_log_write_rejects_missing_files(workspace: Path):
    try:
        log_write(
            cwd=workspace,
            task_id="task-2026-05-25-001",
            session_id="session-1",
            files=["src/auth/missing.ts"],
            summary="文件不存在",
        )
    except FileNotFoundError as exc:
        assert "src/auth/missing.ts" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")


def test_log_write_generates_distinct_event_ids_for_back_to_back_writes(workspace: Path):
    source_file = workspace / "src" / "auth" / "login.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const login = 'ok';\n", encoding="utf-8")

    first = log_write(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        session_id="session-1",
        files=["src/auth/login.ts"],
        summary="第一次记录",
    )
    second = log_write(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        session_id="session-1",
        files=["src/auth/login.ts"],
        summary="第二次记录",
    )

    assert first["event"]["event_id"] != second["event"]["event_id"]
    assert (workspace / first["event_path"]).exists()
    assert (workspace / second["event_path"]).exists()


def test_log_write_cleans_up_partial_snapshots_when_event_write_fails(
    workspace: Path, monkeypatch
):
    source_file = workspace / "src" / "auth" / "login.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const login = 'ok';\n", encoding="utf-8")

    original_dumps = history_store.json.dumps

    def fail_dumps(*args, **kwargs):
        raise RuntimeError("simulated event serialization failure")

    monkeypatch.setattr(history_store.json, "dumps", fail_dumps)

    try:
        log_write(
            cwd=workspace,
            task_id="task-2026-05-25-001",
            session_id="session-1",
            files=["src/auth/login.ts"],
            summary="这次写入应该失败",
        )
    except RuntimeError as exc:
        assert str(exc) == "simulated event serialization failure"
    else:
        raise AssertionError("expected RuntimeError")
    finally:
        monkeypatch.setattr(history_store.json, "dumps", original_dumps)

    snapshots_root = workspace / ".aicore" / "history" / "snapshots"
    events_root = workspace / ".aicore" / "history" / "events"
    assert not snapshots_root.exists() or not any(snapshots_root.rglob("*"))
    assert not events_root.exists() or not any(events_root.iterdir())


def test_log_write_normalizes_windows_style_paths(workspace: Path):
    source_file = workspace / "src" / "auth" / "login.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const login = 'ok';\n", encoding="utf-8")

    result = log_write(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        session_id="session-1",
        files=["src\\auth\\login.ts"],
        summary="Windows 风格路径也应可用",
    )

    assert result["event"]["files"][0]["path"] == "src/auth/login.ts"
    assert "\\" not in result["event"]["files"][0]["snapshot_path"]
    assert (workspace / result["event"]["files"][0]["snapshot_path"]).exists()


def test_log_write_rejects_paths_outside_workspace(workspace: Path):
    try:
        log_write(
            cwd=workspace,
            task_id="task-2026-05-25-001",
            session_id="session-1",
            files=["../outside.ts"],
            summary="路径越界",
        )
    except ValueError as exc:
        assert "工作区" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_log_write_preserves_distinct_snapshots_for_similar_file_names(workspace: Path):
    first_file = workspace / "src" / "a" / "b__c.txt"
    second_file = workspace / "src" / "a__b" / "c.txt"
    first_file.parent.mkdir(parents=True, exist_ok=True)
    second_file.parent.mkdir(parents=True, exist_ok=True)
    first_file.write_text("first", encoding="utf-8")
    second_file.write_text("second", encoding="utf-8")

    result = log_write(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        session_id="session-1",
        files=["src/a/b__c.txt", "src/a__b/c.txt"],
        summary="两个相似路径都要单独保存",
    )

    snapshot_paths = [item["snapshot_path"] for item in result["event"]["files"]]

    assert len(snapshot_paths) == 2
    assert snapshot_paths[0] != snapshot_paths[1]
    assert (workspace / snapshot_paths[0]).read_text(encoding="utf-8") == "first"
    assert (workspace / snapshot_paths[1]).read_text(encoding="utf-8") == "second"


def test_create_checkpoint_persists_manifest(workspace: Path):
    source_file = workspace / "src" / "auth" / "login.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const login = 'ok';\n", encoding="utf-8")

    event_result = log_write(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        session_id="session-1",
        files=["src/auth/login.ts"],
        summary="先创建一个真实事件",
    )

    result = create_checkpoint(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        event_ids=[event_result["event"]["event_id"]],
        summary="阶段性保存当前进度",
    )

    manifest_path = workspace / result["manifest_path"]
    assert manifest_path.exists()
    assert "\\" not in result["manifest_path"]

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest["checkpoint_id"] == result["checkpoint"]["checkpoint_id"]
    assert manifest["task_id"] == "task-2026-05-25-001"
    assert manifest["event_ids"] == [event_result["event"]["event_id"]]
    assert manifest["summary"] == "阶段性保存当前进度"
    assert manifest["timestamp"] == result["checkpoint"]["timestamp"]


def test_create_checkpoint_cleans_up_partial_directory_when_manifest_write_fails(
    workspace: Path, monkeypatch
):
    source_file = workspace / "src" / "auth" / "login.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const login = 'ok';\n", encoding="utf-8")

    event_result = log_write(
        cwd=workspace,
        task_id="task-2026-05-25-001",
        session_id="session-1",
        files=["src/auth/login.ts"],
        summary="先创建真实事件",
    )

    original_dumps = history_store.json.dumps

    def fail_dumps(*args, **kwargs):
        raise RuntimeError("simulated checkpoint serialization failure")

    monkeypatch.setattr(history_store.json, "dumps", fail_dumps)

    try:
        create_checkpoint(
            cwd=workspace,
            task_id="task-2026-05-25-001",
            event_ids=[event_result["event"]["event_id"]],
            summary="这次 checkpoint 应该失败",
        )
    except RuntimeError as exc:
        assert str(exc) == "simulated checkpoint serialization failure"
    else:
        raise AssertionError("expected RuntimeError")
    finally:
        monkeypatch.setattr(history_store.json, "dumps", original_dumps)

    checkpoints_root = workspace / ".aicore" / "history" / "checkpoints"
    assert not checkpoints_root.exists() or not any(checkpoints_root.rglob("*"))


def test_create_checkpoint_rejects_unknown_event_ids(workspace: Path):
    try:
        create_checkpoint(
            cwd=workspace,
            task_id="task-2026-05-25-001",
            event_ids=["event-missing"],
            summary="不应允许引用不存在的事件",
        )
    except FileNotFoundError as exc:
        assert "event-missing" in str(exc)
    else:
        raise AssertionError("expected FileNotFoundError")

    checkpoints_root = workspace / ".aicore" / "history" / "checkpoints"
    assert not checkpoints_root.exists() or not any(checkpoints_root.rglob("*"))


def test_create_checkpoint_rejects_event_ids_from_other_tasks(workspace: Path):
    source_file = workspace / "src" / "auth" / "login.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const login = 'ok';\n", encoding="utf-8")

    event_result = log_write(
        cwd=workspace,
        task_id="task-2026-05-25-002",
        session_id="session-1",
        files=["src/auth/login.ts"],
        summary="属于其他任务的事件",
    )

    try:
        create_checkpoint(
            cwd=workspace,
            task_id="task-2026-05-25-001",
            event_ids=[event_result["event"]["event_id"]],
            summary="不应串用其他任务的事件",
        )
    except ValueError as exc:
        assert "task-2026-05-25-002" in str(exc)
    else:
        raise AssertionError("expected ValueError")

    checkpoints_root = workspace / ".aicore" / "history" / "checkpoints"
    assert not checkpoints_root.exists() or not any(checkpoints_root.rglob("*"))


def test_cli_log_write_and_checkpoint_function_signatures_match_expected_entrypoints():
    assert list(inspect.signature(log_write).parameters) == [
        "cwd",
        "task_id",
        "session_id",
        "files",
        "summary",
    ]
    assert list(inspect.signature(create_checkpoint).parameters) == [
        "cwd",
        "task_id",
        "event_ids",
        "summary",
    ]
