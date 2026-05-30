from aicore.cli import build_parser, main
from pathlib import Path
import os
import subprocess
import sys


def test_build_parser_subcommands_are_exposed_via_help_text():
    parser = build_parser()
    help_text = parser.format_help()

    assert "start" in help_text
    assert "review" in help_text
    assert "approve" in help_text
    assert "reject" in help_text
    assert "log-write" in help_text
    assert "checkpoint" in help_text
    assert "ledger-confirm" in help_text
    assert "status" in help_text


def test_main_without_args_prints_help_and_returns_zero(capsys):
    exit_code = main([])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "start" in captured.out
    assert "approve" in captured.out
    assert "log-write" in captured.out
    assert "ledger-confirm" in captured.out
    assert "status" in captured.out


def test_main_with_missing_task_returns_non_zero_and_prints_task_not_found(capsys):
    exit_code = main(["review", "task-123"])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "task not found" in captured.err.lower()


def test_main_log_write_dispatches_to_history_service(monkeypatch, capsys):
    called: dict[str, object] = {}

    def fake_log_write(*, cwd, task_id, session_id, files, summary):
        called["cwd"] = cwd
        called["task_id"] = task_id
        called["session_id"] = session_id
        called["files"] = files
        called["summary"] = summary
        return {
            "event": {"event_id": "event-001"},
            "event_path": ".aicore/history/events/event-001.json",
        }

    monkeypatch.setattr("aicore.cli.log_write", fake_log_write)

    exit_code = main(
        [
            "log-write",
            "task-2026-05-26-001",
            "--session",
            "session-1",
            "--file",
            "src/auth/login.ts",
            "--file",
            "src/auth/session.ts",
            "--summary",
            "记录改动",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["task_id"] == "task-2026-05-26-001"
    assert called["session_id"] == "session-1"
    assert called["files"] == ["src/auth/login.ts", "src/auth/session.ts"]
    assert called["summary"] == "记录改动"
    assert captured.out == "event-001\n.aicore/history/events/event-001.json\n"


def test_main_checkpoint_dispatches_to_history_service(monkeypatch, capsys):
    called: dict[str, object] = {}

    def fake_create_checkpoint(*, cwd, task_id, event_ids, summary):
        called["cwd"] = cwd
        called["task_id"] = task_id
        called["event_ids"] = event_ids
        called["summary"] = summary
        return {
            "checkpoint": {"checkpoint_id": "checkpoint-001"},
            "manifest_path": ".aicore/history/checkpoints/checkpoint-001/manifest.json",
        }

    monkeypatch.setattr("aicore.cli.create_checkpoint", fake_create_checkpoint)

    exit_code = main(
        [
            "checkpoint",
            "task-2026-05-26-001",
            "--event",
            "event-001",
            "--event",
            "event-002",
            "--summary",
            "保存阶段进度",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["task_id"] == "task-2026-05-26-001"
    assert called["event_ids"] == ["event-001", "event-002"]
    assert called["summary"] == "保存阶段进度"
    assert (
        captured.out
        == "checkpoint-001\n.aicore/history/checkpoints/checkpoint-001/manifest.json\n"
    )


def test_main_ledger_confirm_dispatches_to_ledger_service(monkeypatch, capsys):
    called: dict[str, object] = {}

    def fake_confirm_ledger_entry(
        *,
        cwd,
        task_id,
        event_ref,
        capability,
        entrypoint,
        limit,
        compatibility,
        risk,
    ):
        called["cwd"] = cwd
        called["task_id"] = task_id
        called["event_ref"] = event_ref
        called["capability"] = capability
        called["entrypoint"] = entrypoint
        called["limit"] = limit
        called["compatibility"] = compatibility
        called["risk"] = risk
        return {"ledger_path": ".aicore/system-ledger.md"}

    monkeypatch.setattr("aicore.cli.confirm_ledger_entry", fake_confirm_ledger_entry)

    exit_code = main(
        [
            "ledger-confirm",
            "task-2026-05-26-001",
            "--event",
            "event-001",
            "--capability",
            "支持完成态账本记录",
            "--entrypoint",
            "ledger-confirm",
            "--limit",
            "当前仅支持单文件账本",
            "--compatibility",
            "兼容 macOS、Windows、Linux",
            "--risk",
            "重复确认会持续追加",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["task_id"] == "task-2026-05-26-001"
    assert called["event_ref"] == "event-001"
    assert called["capability"] == "支持完成态账本记录"
    assert called["entrypoint"] == "ledger-confirm"
    assert called["limit"] == "当前仅支持单文件账本"
    assert called["compatibility"] == "兼容 macOS、Windows、Linux"
    assert called["risk"] == "重复确认会持续追加"
    assert captured.out == ".aicore/system-ledger.md\n"


def test_main_status_dispatches_to_status_service(monkeypatch, capsys):
    def fake_build_status(cwd):
        return {
            "sessions": ["claude-20260530", "codex-20260530"],
            "checkpointed_event_ids": ["event-checked"],
            "pending_event_ids": ["event-pending"],
            "multi_session_file_risks": [
                {
                    "path": "README.md",
                    "sessions": ["claude-20260530", "codex-20260530"],
                    "event_ids": ["event-checked", "event-pending"],
                }
            ],
        }

    monkeypatch.setattr("aicore.cli.build_status", fake_build_status)

    exit_code = main(["status"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "Sessions" in captured.out
    assert "claude-20260530" in captured.out
    assert "Pending Events" in captured.out
    assert "event-pending" in captured.out
    assert "Multi-session File Risks" in captured.out
    assert "README.md" in captured.out


def test_main_log_write_reports_service_errors_without_traceback(monkeypatch, capsys):
    def fail_log_write(**kwargs):
        raise FileNotFoundError("src/auth/missing.ts")

    monkeypatch.setattr("aicore.cli.log_write", fail_log_write)

    exit_code = main(
        [
            "log-write",
            "task-2026-05-26-001",
            "--session",
            "session-1",
            "--file",
            "src/auth/missing.ts",
            "--summary",
            "记录改动",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 1
    assert "error: src/auth/missing.ts" in captured.err


def test_main_checkpoint_reports_service_errors_without_traceback(monkeypatch, capsys):
    def fail_create_checkpoint(**kwargs):
        raise ValueError("event_ids 不能为空")

    monkeypatch.setattr("aicore.cli.create_checkpoint", fail_create_checkpoint)

    exit_code = main(
        [
            "checkpoint",
            "task-2026-05-26-001",
            "--event",
            "event-001",
            "--summary",
            "保存阶段进度",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "error: event_ids 不能为空" in captured.err


def test_main_ledger_confirm_reports_service_errors_without_traceback(
    monkeypatch, capsys
):
    def fail_confirm_ledger_entry(**kwargs):
        raise ValueError("capability 必须是单行文本")

    monkeypatch.setattr("aicore.cli.confirm_ledger_entry", fail_confirm_ledger_entry)

    exit_code = main(
        [
            "ledger-confirm",
            "task-2026-05-26-001",
            "--event",
            "event-001",
            "--capability",
            "坏输入",
            "--entrypoint",
            "ledger-confirm",
            "--limit",
            "当前仅支持单文件账本",
            "--compatibility",
            "兼容 macOS、Windows、Linux",
            "--risk",
            "重复确认会持续追加",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "error: capability 必须是单行文本" in captured.err


def test_python_m_entrypoint_executes_cli_commands(workspace: Path):
    source_file = workspace / "src" / "auth" / "login.ts"
    source_file.parent.mkdir(parents=True, exist_ok=True)
    source_file.write_text("export const login = 'ok';\n", encoding="utf-8")

    env = os.environ.copy()
    src_path = str(Path(__file__).resolve().parents[1] / "src")
    env["PYTHONPATH"] = src_path + os.pathsep + env.get("PYTHONPATH", "")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "aicore.cli",
            "log-write",
            "task-2026-05-26-001",
            "--session",
            "session-1",
            "--file",
            "src/auth/login.ts",
            "--summary",
            "记录登录改动",
        ],
        cwd=workspace,
        env=env,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "event-" in result.stdout
    assert ".aicore/history/events/" in result.stdout
