from aicore.cli import (
    build_parser,
    main,
    shortcut_approve,
    shortcut_checklist,
    shortcut_list,
    shortcut_show,
    shortcut_start,
    shortcut_update,
)
from pathlib import Path
import os
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_build_parser_subcommands_are_exposed_via_help_text():
    parser = build_parser()
    help_text = parser.format_help()

    assert "start" in help_text
    assert "list" in help_text
    assert "show" in help_text
    assert "checklist" in help_text
    assert "update" in help_text
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
    assert "list" in captured.out
    assert "show" in captured.out
    assert "checklist" in captured.out
    assert "update" in captured.out
    assert "approve" in captured.out
    assert "log-write" in captured.out
    assert "ledger-confirm" in captured.out
    assert "status" in captured.out


def test_main_with_missing_task_returns_non_zero_and_prints_task_not_found(capsys):
    exit_code = main(["review", "task-123"])
    captured = capsys.readouterr()

    assert exit_code != 0
    assert "task not found" in captured.err.lower()


def test_main_show_with_missing_task_returns_non_zero_and_prints_task_not_found(capsys):
    exit_code = main(["show", "task-123"])
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


def test_main_list_dispatches_to_task_query_service(monkeypatch, capsys):
    def fake_list_tasks(cwd):
        return [
            {
                "id": "task-2026-05-26-001",
                "status": "draft",
                "scope": {"module": "auth-login"},
                "request": {"raw": "实现 JWT 登录"},
            }
        ]

    monkeypatch.setattr("aicore.cli.list_tasks", fake_list_tasks)

    exit_code = main(["list"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "task-2026-05-26-001" in captured.out
    assert "draft" in captured.out
    assert "auth-login" in captured.out


def test_main_show_dispatches_to_task_query_service(monkeypatch, capsys):
    def fake_get_task(task_id, cwd):
        return {
            "id": task_id,
            "status": "approved",
            "project": {"type": "product-delivery"},
            "scope": {"module": "auth-login"},
            "request": {"raw": "实现 JWT 登录"},
            "entrypoints": {"main": [], "compat": []},
            "implementation": {
                "dual_write_required": False,
                "dual_write_reason": "待确认是否存在兼容入口或双实现。",
            },
            "change_scope": {"allowed_files": [], "protected_areas": ["禁止修改发布链路"]},
            "acceptance": {"baseline_refs": []},
            "context": {"rollback_plan": "直接 reject 并重建草案"},
        }

    monkeypatch.setattr("aicore.cli.get_task", fake_get_task)

    exit_code = main(["show", "task-2026-05-26-001"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "task-2026-05-26-001" in captured.out
    assert "状态: approved" in captured.out
    assert "原始需求: 实现 JWT 登录" in captured.out


def test_main_checklist_dispatches_to_contract_service(monkeypatch, capsys):
    def fake_build_contract_checklist(task_id, cwd):
        return {
            "task": {"id": task_id, "status": "draft"},
            "items": [
                {
                    "title": "主入口已确认",
                    "ok": False,
                    "hint": "请补充 --main-entrypoint，明确这次到底改哪个入口。",
                }
            ],
            "ready": False,
            "failed_items": [],
        }

    def fake_render_contract_checklist(report):
        return "task-2026-05-26-001\n状态: draft\n审批契约检查"

    monkeypatch.setattr("aicore.cli.build_contract_checklist", fake_build_contract_checklist)
    monkeypatch.setattr("aicore.cli.render_contract_checklist", fake_render_contract_checklist)

    exit_code = main(["checklist", "task-2026-05-26-001"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert "审批契约检查" in captured.out


def test_main_update_dispatches_to_task_update_service(monkeypatch, capsys):
    called: dict[str, object] = {}

    def fake_update_task(task_id, cwd, **kwargs):
        called["task_id"] = task_id
        called["kwargs"] = kwargs
        return {
            "id": task_id,
            "status": "draft",
            "project": {"type": "product-delivery"},
            "scope": {"module": "auth-login"},
            "request": {"raw": "实现 JWT 登录"},
            "entrypoints": {"main": ["API: POST /auth/login"], "compat": []},
            "implementation": {
                "dual_write_required": False,
                "dual_write_reason": "当前仅改 API 主入口。",
            },
            "change_scope": {
                "allowed_files": ["src/auth/login.ts"],
                "protected_areas": ["禁止修改发布链路"],
            },
            "acceptance": {"baseline_refs": ["tests/test_auth.py"]},
            "context": {"rollback_plan": "回滚到上一版实现"},
        }

    monkeypatch.setattr("aicore.cli.update_task", fake_update_task)

    exit_code = main(
        [
            "update",
            "task-2026-05-26-001",
            "--main-entrypoint",
            "API: POST /auth/login",
            "--allowed-file",
            "src/auth/login.ts",
            "--baseline-ref",
            "tests/test_auth.py",
            "--success-criteria",
            "登录成功路径通过",
            "--review-summary",
            "主入口与修改范围已确认",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert called["task_id"] == "task-2026-05-26-001"
    assert called["kwargs"]["main_entrypoints"] == ["API: POST /auth/login"]
    assert called["kwargs"]["allowed_files"] == ["src/auth/login.ts"]
    assert called["kwargs"]["baseline_refs"] == ["tests/test_auth.py"]
    assert called["kwargs"]["success_criteria"] == ["登录成功路径通过"]
    assert called["kwargs"]["review_summary"] == "主入口与修改范围已确认"
    assert "状态: draft" in captured.out


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


def test_repo_root_python_m_entrypoint_works_without_pythonpath():
    result = subprocess.run(
        [sys.executable, "-m", "aicore.cli"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "start" in result.stdout
    assert "update" in result.stdout
    assert "ledger-confirm" in result.stdout


def test_repo_bin_shortcut_works_without_pythonpath():
    result = subprocess.run(
        ["./bin/aicore", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "start" in result.stdout
    assert "update" in result.stdout
    assert "ledger-confirm" in result.stdout


def test_repo_bin_checklist_shortcut_works_without_pythonpath():
    result = subprocess.run(
        ["./bin/acheck", "--help"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    assert "checklist" in result.stdout


def test_installed_shortcut_entrypoints_forward_to_main(monkeypatch):
    calls: list[list[str]] = []

    def fake_main(argv=None):
        calls.append(list(argv or []))
        return 0

    monkeypatch.setattr("aicore.cli.main", fake_main)
    monkeypatch.setattr("sys.argv", ["astart", "实现 JWT 登录"])
    assert shortcut_start() == 0
    monkeypatch.setattr("sys.argv", ["alist"])
    assert shortcut_list() == 0
    monkeypatch.setattr("sys.argv", ["ashow", "task-1"])
    assert shortcut_show() == 0
    monkeypatch.setattr("sys.argv", ["acheck", "task-1"])
    assert shortcut_checklist() == 0
    monkeypatch.setattr("sys.argv", ["aupdate", "task-1", "--risk", "异常路径未覆盖"])
    assert shortcut_update() == 0
    monkeypatch.setattr("sys.argv", ["aapprove", "task-1", "--by", "h12"])
    assert shortcut_approve() == 0

    assert calls == [
        ["start", "实现 JWT 登录"],
        ["list"],
        ["show", "task-1"],
        ["checklist", "task-1"],
        ["update", "task-1", "--risk", "异常路径未覆盖"],
        ["approve", "task-1", "--by", "h12"],
    ]
