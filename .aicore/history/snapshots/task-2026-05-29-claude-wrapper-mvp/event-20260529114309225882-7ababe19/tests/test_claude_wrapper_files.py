from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_project_claude_instructions_define_aicore_state_contract():
    claude_file = PROJECT_ROOT / "CLAUDE.md"

    assert claude_file.exists()

    text = claude_file.read_text(encoding="utf-8")

    assert "aicore start" in text
    assert "log-write" in text
    assert "checkpoint" in text
    assert "ledger-confirm" in text
    assert "不维护第二套状态" in text


def test_claude_commands_cover_the_four_aicore_entrypoints():
    commands = {
        "aicore-start.md": "python3.11 -m aicore.cli start",
        "aicore-log-write.md": "python3.11 -m aicore.cli log-write",
        "aicore-checkpoint.md": "python3.11 -m aicore.cli checkpoint",
        "aicore-ledger.md": "python3.11 -m aicore.cli ledger-confirm",
        "aicore-save.md": "python3.11 -m aicore.cli log-write",
    }

    for filename, command_text in commands.items():
        text = (PROJECT_ROOT / ".claude" / "commands" / filename).read_text(
            encoding="utf-8"
        )

        assert command_text in text
        assert "Python 3.11 启动器" in text
        assert "何时使用" in text
        assert "输出" in text
        assert "不要" in text


def test_aicore_guard_agent_is_supervisory_not_autonomous():
    text = (PROJECT_ROOT / ".claude" / "agents" / "aicore-guard.md").read_text(
        encoding="utf-8"
    )

    assert "流程监督" in text
    assert "python3.11 -m aicore.cli" in text
    assert "不自动批准" in text
    assert "不自动提交 Git" in text
    assert "不自行扩大修改范围" in text
    assert "不维护第二套状态" in text
    assert "system-ledger.md" in text


def test_aicore_save_command_combines_history_and_checkpoint_only():
    text = (PROJECT_ROOT / ".claude" / "commands" / "aicore-save.md").read_text(
        encoding="utf-8"
    )

    assert "小改动" in text
    assert "python3.11 -m aicore.cli log-write" in text
    assert "python3.11 -m aicore.cli checkpoint" in text
    assert "不写 ledger" in text
    assert "event-id" in text
    assert "checkpoint-id" in text


def test_aicore_ledger_command_is_plan_driven():
    text = (PROJECT_ROOT / ".claude" / "commands" / "aicore-ledger.md").read_text(
        encoding="utf-8"
    )

    assert "已批准 plan" in text
    assert "计划项" in text
    assert "不要凭聊天记忆" in text


def test_claude_settings_register_post_tool_save_reminder_hook():
    settings = json.loads(
        (PROJECT_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
    )

    post_tool_hooks = settings["hooks"]["PostToolUse"]
    hook_config = post_tool_hooks[0]

    assert hook_config["matcher"] == "Write|Edit|MultiEdit"
    assert hook_config["hooks"][0]["type"] == "command"
    assert ".claude/hooks/aicore_save_reminder.py" in hook_config["hooks"][0]["command"]


def test_aicore_save_reminder_hook_prompts_after_file_write():
    hook_path = PROJECT_ROOT / ".claude" / "hooks" / "aicore_save_reminder.py"
    payload = {"tool_name": "Write", "tool_input": {"file_path": "README.md"}}

    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "/aicore-save" in result.stderr
    assert "README.md" in result.stderr


def test_aicore_save_reminder_hook_ignores_aicore_internal_writes():
    hook_path = PROJECT_ROOT / ".claude" / "hooks" / "aicore_save_reminder.py"
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": ".aicore/system-ledger.md"},
    }

    result = subprocess.run(
        [sys.executable, str(hook_path)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""


def test_readme_mentions_claude_code_wrapper_entrypoints():
    text = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

    assert "Claude Code" in text
    assert "/aicore-start" in text
    assert "/aicore-save" in text
    assert "/aicore-log-write" in text
    assert "/aicore-checkpoint" in text
    assert "/aicore-ledger" in text
    assert "PostToolUse" in text
